"""Owned scans, immutable commit snapshots and real evidence acquisition."""
from __future__ import annotations
import ast
import os
import re
import subprocess
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from schemas.scan import ScanRequest, ScanResponse, SensorResult, DiscoveredRoute
from schemas.correlation import CorrelationRequest
from services.analyzers import run_analyzer
from services.runtime_service import runtime_probe
from services.langgraph_pipeline import run_workflow
from services.mongodb_service import save_scan, get_scan as db_scan, list_scans as db_scans

SCAN_STORE: dict[tuple[str, str], ScanResponse] = {}
_LOCK = threading.RLock()
_JOBS = ThreadPoolExecutor(max_workers=2, thread_name_prefix="traceguard")
_SLOTS = threading.BoundedSemaphore(4)


def _validate_repository_url(url: str):
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.port not in {None,443}
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", parsed.path)):
        raise ValueError("Use a public https://github.com/owner/repository URL")


def git(args, root=None):
    env = {k:v for k,v in os.environ.items() if k.upper() in {"PATH","SYSTEMROOT","WINDIR","TEMP","TMP","HOME"}}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_LFS_SKIP_SMUDGE="1")
    result = subprocess.run(["git", "-c", "credential.helper=", "-c", "core.hooksPath="+os.devnull,
                             "-c", "protocol.file.allow=never", *args], cwd=root, env=env,
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    if result.returncode:
        raise ValueError("Repository checkout failed: " + result.stderr[-500:])
    return result.stdout.strip()


def _clone(request: ScanRequest, target: Path, commit: str | None = None):
    _validate_repository_url(str(request.repository_url))
    git(["clone", "--depth=1", "--single-branch", "--branch", request.branch, "--", str(request.repository_url), str(target)])
    if commit:
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("Invalid commit SHA")
        git(["fetch", "--depth=1", "origin", commit], target)
        git(["checkout", "--detach", commit], target)
    return git(["rev-parse", "HEAD"], target)


def _discover_python_routes(root: Path) -> tuple[str | None, list[DiscoveredRoute]]:
    routes: list[DiscoveredRoute] = []
    framework: str | None = None
    for path in root.rglob("*.py"):
        if any(
            part in {".git", ".venv", "venv", "node_modules"} for part in path.parts
        ):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        imports = {
            alias.name.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports |= {
            alias.module.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module
            for alias in [node]
        }
        if "fastapi" in imports:
            framework = framework or "fastapi"
        if "flask" in imports:
            framework = framework or "flask"
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(
                    decorator.func, ast.Attribute
                ):
                    continue
                if decorator.func.attr not in {
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "route",
                }:
                    continue
                if not decorator.args or not isinstance(
                    decorator.args[0], ast.Constant
                ):
                    continue
                path_value = str(decorator.args[0].value)
                method = decorator.func.attr.upper()
                if method == "ROUTE":
                    method = "GET"
                routes.append(
                    DiscoveredRoute(
                        method=method,
                        path=path_value,
                        function=node.name,
                        framework=framework or "python",
                        file=path.relative_to(root).as_posix(), line=node.lineno,
                    )
                )
    return framework, routes



def attach_functions(root, findings):
    cache = {}
    for finding in findings:
        if not finding.location or not finding.location.line:
            continue
        path = (root / finding.location.file).resolve()
        if not path.is_relative_to(root.resolve()) or path.suffix != ".py" or not path.is_file():
            continue
        try:
            if path not in cache:
                cache[path] = ast.parse(path.read_text(encoding="utf-8"))
            funcs = [n for n in ast.walk(cache[path]) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.lineno <= finding.location.line <= (n.end_lineno or n.lineno)]
            if funcs:
                finding.location.function = min(funcs, key=lambda n:(n.end_lineno or n.lineno)-n.lineno).name
        except (SyntaxError, UnicodeError, OSError):
            pass
    return findings


def _save(scan, uid):
    save_scan(scan.model_dump(mode="json"), uid)
    with _LOCK:
        SCAN_STORE[(uid,scan.scan_id)] = scan.model_copy(deep=True)


def get_scan(scan_id: str, firebase_uid: str):
    with _LOCK:
        cached = SCAN_STORE.get((firebase_uid,scan_id))
        if cached:
            return cached.model_copy(deep=True)
    stored = db_scan(scan_id, firebase_uid)
    return ScanResponse.model_validate(stored) if stored else None


def list_scans(firebase_uid: str):
    persisted = {s["scan_id"]:ScanResponse.model_validate(s) for s in db_scans(firebase_uid)}
    with _LOCK:
        persisted.update({sid:s.model_copy(deep=True) for (uid,sid),s in SCAN_STORE.items() if uid==firebase_uid})
    return sorted(persisted.values(), key=lambda s:s.started_at, reverse=True)


def scan_repository(request: ScanRequest, firebase_uid: str, scan: ScanResponse | None = None):
    if not request.authorized:
        raise PermissionError("Confirm repository testing authorization")
    scan = scan or ScanResponse(scan_id="scan-"+uuid.uuid4().hex, repository_url=str(request.repository_url),
        branch=request.branch, started_at=datetime.now(timezone.utc).isoformat(), runtime_enabled=request.runtime_enabled,
        runtime_entrypoint=request.runtime_entrypoint)
    scan.status = "RUNNING"
    _save(scan, firebase_uid)
    try:
        with tempfile.TemporaryDirectory(prefix="traceguard-") as workspace:
            root = Path(workspace)/"repo"
            scan.commit_sha = _clone(request, root)
            scan.framework, scan.routes = _discover_python_routes(root)
            initial = []
            # Independent fast sensors first; deep sensors are scheduled by research or explicitly below.
            for tool in ("semgrep", "gitleaks", "osv-scanner", "trivy"):
                findings, sensor = run_analyzer(tool, root)
                initial.extend(findings)
                scan.sensors.append(sensor)
                _save(scan, firebase_uid)
            if request.runtime_enabled:
                findings, sensor = runtime_probe(root, scan.framework, scan.routes, request.runtime_entrypoint)
                initial.extend(findings)
                scan.sensors.append(sensor)
            initial = attach_functions(root, list({f.finding_id:f for f in initial}.values()))
            acquired = set()
            def research(feedback, round_number):
                additional = []
                tools = [tool for tool in ("codeql","joern") if tool not in acquired]
                for tool in tools:
                    values, sensor = run_analyzer(tool, root, research=True)
                    acquired.add(tool)
                    additional.extend(values)
                    scan.sensors.append(sensor)
                    _save(scan, firebase_uid)
                if request.runtime_enabled and "mutations" not in acquired:
                    values, sensor = runtime_probe(root, scan.framework, scan.routes, request.runtime_entrypoint, mutate=True)
                    acquired.add("mutations")
                    additional.extend(values)
                    scan.sensors.append(sensor)
                return attach_functions(root, additional)
            if not request.research_again or request.max_research_rounds == 0:
                initial.extend(research([], 0))
            from services.remediation_service import source_context
            scan.report = run_workflow(CorrelationRequest(findings=initial, research_again=request.research_again,
                max_research_rounds=request.max_research_rounds, generate_patches=True,
                feedback=["Collect independent CodeQL/Joern evidence and controlled runtime mutations"] if request.research_again else []),
                researcher=research, context_provider=lambda f:source_context(root, f))
            scan.findings_count = len(scan.report.findings)
            scan.high_risk_count = sum(f.severity in {"critical","high"} for f in scan.report.findings)
            scan.status = "FAILED" if any(s.status=="FAILED" for s in scan.sensors) else "COMPLETED"
            if scan.status == "FAILED":
                scan.error = "Analysis is incomplete: inspect failed sensors. Available findings are retained."
    except Exception as error:
        scan.status, scan.error = "FAILED", str(error)[:1000]
    scan.completed_at = datetime.now(timezone.utc).isoformat()
    _save(scan, firebase_uid)
    return scan


def enqueue_scan(request: ScanRequest, uid: str):
    if not request.authorized:
        raise PermissionError("Confirm repository testing authorization")
    _validate_repository_url(str(request.repository_url))
    if not _SLOTS.acquire(blocking=False):
        raise RuntimeError("Scan queue is full; retry after an active scan completes")
    scan = ScanResponse(scan_id="scan-"+uuid.uuid4().hex, repository_url=str(request.repository_url), branch=request.branch,
        started_at=datetime.now(timezone.utc).isoformat(), status="QUEUED", runtime_enabled=request.runtime_enabled,
        runtime_entrypoint=request.runtime_entrypoint)
    try:
        _save(scan, uid)
        def work():
            try:
                scan_repository(request, uid, scan)
            finally:
                _SLOTS.release()
        _JOBS.submit(work)
    except Exception:
        _SLOTS.release()
        raise
    return scan.model_copy(deep=True)
