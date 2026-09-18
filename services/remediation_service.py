"""Reviewable patches validated on the original commit, never the user's checkout."""
from __future__ import annotations
import json
import os
import re
import tempfile
import threading
import uuid
from pathlib import Path, PurePosixPath
from schemas.remediation import FixRequest, FixAttempt
from schemas.scan import ScanRequest
from services.analyzers import run_analyzer, IMAGES
from services.sandbox import run_container
from services.correlation_service import _correlation_key


def source_context(root: Path, finding) -> str:
    if not finding.location or "gitleaks" in finding.source_tools:
        return ""
    path = (root / finding.location.file).resolve()
    if not path.is_relative_to(root.resolve()) or path.suffix != ".py" or not path.is_file() or path.is_symlink():
        return ""
    if path.stat().st_size > 64000:
        return ""
    return "FILE: " + finding.location.file + "\n" + path.read_text(encoding="utf-8", errors="replace")[:12000]


def validate_patch(diff: str, allowed_file: str) -> None:
    """V1 only edits the finding's existing Python source, never tests or configuration."""
    path = PurePosixPath(allowed_file)
    if (path.is_absolute() or ".." in path.parts or "\\" in allowed_file or ":" in allowed_file
        or path.suffix != ".py" or any(p.startswith(".") for p in path.parts)
        or any(p.lower() in {"tests", "test"} for p in path.parts) or path.name.startswith("test_")):
        raise ValueError("Only the finding's existing Python source file may be patched")
    if not diff or len(diff) > 50000 or "\x00" in diff:
        raise ValueError("A bounded unified diff is required")
    if any(marker in diff for marker in ("GIT binary patch", "rename from", "rename to", "new file mode", "deleted file mode", "old mode", "new mode")):
        raise ValueError("File creation/deletion, renames, mode changes and binary patches are not allowed")
    old = re.findall(r"^--- (.+)$", diff, re.M)
    new = re.findall(r"^\+\+\+ (.+)$", diff, re.M)
    if old != ["a/"+allowed_file] or new != ["b/"+allowed_file] or not re.search(r"^@@ .* @@",diff,re.M):
        raise ValueError("Diff must modify exactly the finding's source file with a/ and b/ headers")
    headers = re.findall(r"^diff --git (.+)$",diff,re.M)
    if headers and headers != ["a/"+allowed_file+" b/"+allowed_file]:
        raise ValueError("Unexpected diff file header")


def _validate_fix(scan_id: str, uid: str, payload: FixRequest):
    from services.scan_service import get_scan, _clone, _save, git, attach_functions
    from services.runtime_service import runtime_probe
    scan = get_scan(scan_id, uid)
    if not scan or not scan.commit_sha:
        raise LookupError("Completed scan not found")
    if scan.status in {"QUEUED", "RUNNING"}:
        raise ValueError("Wait for scan completion")
    finding = next((f for f in scan.report.findings if f.finding_id == payload.finding_id),None)
    if not finding or not finding.location:
        raise LookupError("Finding not found")
    diff = payload.unified_diff or (finding.patch.unified_diff if finding.patch else None)
    validate_patch(diff or "", finding.location.file)
    attempt = FixAttempt(fix_id="fix-"+uuid.uuid4().hex, finding_id=finding.finding_id,
                         commit_sha=scan.commit_sha, unified_diff=diff)
    scan.fixes.append(attempt)
    _save(scan,uid)
    try:
        with tempfile.TemporaryDirectory(prefix="traceguard-fix-") as directory:
            root = Path(directory)/"repo"
            request = ScanRequest(repository_url=scan.repository_url, branch=scan.branch, authorized=True)
            _clone(request,root,scan.commit_sha)
            target = (root/finding.location.file).resolve()
            if not target.is_relative_to(root.resolve()) or target.is_symlink() or not target.is_file():
                raise ValueError("Patch target is not a regular repository file")
            image = os.getenv("TRACEGUARD_RUNTIME_IMAGE", "traceguard/runtime:local")
            checked = run_container(image,["python","/opt/traceguard/validate.py"],root,
                extra={"patch.diff":diff.encode(), "regression.py":(payload.regression_test or (finding.patch.regression_test if finding.patch else None) or "").encode()},output_file="/workspace/out/validation.json",timeout=900)
            if checked.exit_code or not checked.output:
                raise ValueError("Patch validation worker did not produce a successful report")
            checks = json.loads(checked.output)
            attempt.checks = {name:checks.get(name) is True for name in ("baseline_tests","apply","build","tests","regression_fails_before","regression_passes_after")}
            if not all(attempt.checks.values()):
                attempt.details.append("Patch must apply, compile, and pass existing tests. A security regression must fail before and pass after the patch. Missing tests cannot verify a fix.")
                attempt.status = "FAILED"
            else:
                # This checkout is disposable; git apply parses data and executes no repository code.
                patch_path = Path(directory)/"candidate.diff"
                patch_path.write_text(diff,encoding="utf-8")
                git(["apply","--ignore-space-change","--check","--",str(patch_path)],root)
                git(["apply","--ignore-space-change","--",str(patch_path)],root)
                after = []
                sensors = []
                latest_sensors = {s.name:s for s in scan.sensors}
                original_complete = {name for name,s in latest_sensors.items() if s.status=="COMPLETED"}
                for tool in IMAGES:
                    values,sensor = run_analyzer(tool,root,research=True,image_override=latest_sensors[tool].image if tool in latest_sensors and latest_sensors[tool].status=="COMPLETED" else None)
                    after.extend(values)
                    sensors.append(sensor)
                if scan.runtime_enabled:
                    values,sensor = runtime_probe(root,scan.framework,scan.routes,scan.runtime_entrypoint,mutate=True)
                    after.extend(values)
                    sensors.append(sensor)
                after = attach_functions(root,after)
                attempt.sensors = [s.model_dump() for s in sensors]
                required = set(IMAGES) | ({"runtime"} if scan.runtime_enabled else set())
                attempt.checks["scanner_coverage"] = required <= original_complete and all(s.status=="COMPLETED" for s in sensors)
                attempt.checks["original_finding_absent"] = finding.correlation_key not in {_correlation_key(f) for f in after}
                original_keys = {f.correlation_key for f in scan.report.findings}
                attempt.checks["no_new_findings"] = not any(_correlation_key(f) not in original_keys for f in after)
                attempt.status = "VERIFIED" if all(attempt.checks.values()) else "NOT_VERIFIED"
                attempt.details.append("Verified means the bounded checks passed for this exact commit; it is not proof that the application has no vulnerabilities.")
                if not attempt.checks["scanner_coverage"]:
                    attempt.details.append("Incomplete original or post-fix scanner coverage prevents verification.")
    except Exception as error:
        attempt.status="FAILED"
        attempt.details.append(str(error)[:1000])
    _save(scan,uid)
    return attempt

_FIX_SLOTS = threading.BoundedSemaphore(1)

def validate_fix(scan_id: str, uid: str, payload: FixRequest):
    if not _FIX_SLOTS.acquire(blocking=False):
        raise ValueError("A fix validation is already running; try again after it completes")
    try:
        return _validate_fix(scan_id,uid,payload)
    finally:
        _FIX_SLOTS.release()
