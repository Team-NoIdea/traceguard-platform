"""Real scanner adapters and strict, secret-redacting normalization."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote
from schemas.finding import Evidence, Location, SecurityFinding, StaticEvidence
from schemas.scan import SensorResult
from services.sandbox import SandboxError, run_container

IMAGES = {
    "semgrep": "semgrep/semgrep@sha256:34ab619bf1391a24bfda3f05debd0d8a6ce3093c2d5f9d39cfc00f83c1397823",
    "codeql": "traceguard/codeql:local",
    "joern": "traceguard/joern:local",
    "gitleaks": "zricethezav/gitleaks:v8.24.3",
    "osv-scanner": "ghcr.io/google/osv-scanner:v2.2.2",
    "trivy": "aquasec/trivy:0.69.3",
}


def relative_path(value: str) -> str:
    value = unquote(value).replace("\\", "/")
    for prefix in ("file:///workspace/src/", "/workspace/src/", "/src/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.removeprefix("./")


def finding(tool, rule, file, line, message, severity="medium", cwes=None, flow=None, kind=None):
    file = relative_path(file or "unknown")
    cwes = sorted(set(re.findall(r"CWE-\d+", " ".join(cwes or []), re.I)))
    cwes = [c.upper() for c in cwes]
    identity = "|".join(map(str, [tool, rule, file, line, kind]))
    location = Location(file=file, line=line)
    return SecurityFinding(
        finding_id=tool + "-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
        title=str(message)[:500], type=kind or (cwes[0] if cwes else rule),
        severity=severity if severity in {"critical", "high", "medium", "low", "info"} else "medium",
        cwe=cwes, location=location, source_tools=[tool],
        static_evidence=[StaticEvidence(tool=tool, rule_id=rule, location=location,
            evidence=Evidence(description=str(message)[:2000], flow=flow or [],
                              source=(flow[0] if flow else None), sink=(flow[-1] if flow else None)))])


def sarif(tool: str, payload: dict) -> list[SecurityFinding]:
    if not isinstance(payload.get("runs"), list):
        raise ValueError("Missing SARIF runs")
    findings = []
    for run in payload["runs"]:
        if any(inv.get("executionSuccessful") is False for inv in run.get("invocations", [])):
            raise ValueError("Analyzer reported an incomplete invocation")
        rules = {r["id"]: r for r in run.get("tool", {}).get("driver", {}).get("rules", [])}
        for item in run.get("results", []):
            rule = rules.get(item.get("ruleId"), {})
            props = rule.get("properties", {})
            loc = (item.get("locations") or [{}])[0].get("physicalLocation", {})
            line = loc.get("region", {}).get("startLine")
            file = loc.get("artifactLocation", {}).get("uri", "unknown")
            level = item.get("level", rule.get("defaultConfiguration", {}).get("level", "warning"))
            severity = {"error":"high", "warning":"medium", "note":"low", "none":"info"}.get(level, "medium")
            try:
                score = float(props.get("security-severity", 0))
                if score >= 9: severity = "critical"
                elif score >= 7: severity = "high"
            except (TypeError, ValueError):
                pass
            flow = []
            for code_flow in item.get("codeFlows", []):
                for thread in code_flow.get("threadFlows", []):
                    for step in thread.get("locations", []):
                        location = step.get("location", {})
                        physical = location.get("physicalLocation", {})
                        flow.append(relative_path(physical.get("artifactLocation", {}).get("uri", file)) + ":" + str(physical.get("region", {}).get("startLine", "")) + " " + location.get("message", {}).get("text", ""))
            findings.append(finding(tool, item.get("ruleId", tool), file, line,
                item.get("message", {}).get("text", item.get("ruleId", tool)), severity,
                props.get("tags", []), flow))
    return findings


def normalize(tool: str, payload) -> list[SecurityFinding]:
    if tool == "codeql":
        return sarif(tool, payload)
    if tool == "semgrep":
        if not isinstance(payload, dict) or "results" not in payload:
            raise ValueError("Missing Semgrep results")
        if payload.get("errors"):
            raise ValueError("Semgrep reported parse/scan errors; scan is incomplete")
        result = []
        for item in payload["results"]:
            extra = item.get("extra", {})
            meta = extra.get("metadata", {})
            cwe = meta.get("cwe", [])
            result.append(finding(tool, item["check_id"], item.get("path"), item.get("start", {}).get("line"),
                extra.get("message", item["check_id"]), {"ERROR":"high", "WARNING":"medium", "INFO":"low"}.get(extra.get("severity"), "medium"),
                cwe if isinstance(cwe, list) else [cwe]))
        return result
    if tool == "gitleaks":
        if not isinstance(payload, list):
            raise ValueError("Invalid Gitleaks report")
        # Deliberately discard Secret, Match, entropy and raw source snippets.
        return [finding(tool, item["RuleID"], item.get("File"), item.get("StartLine"),
            "Potential exposed credential: " + item["RuleID"], "high", ["CWE-798"]) for item in payload]
    if tool == "joern":
        if not isinstance(payload, dict) or "findings" not in payload:
            raise ValueError("Invalid Joern report")
        return [finding(tool, item["rule"], item["file"], item.get("line"), item["message"],
            "high", [item["cwe"]], item.get("flow", [])) for item in payload["findings"]]
    if tool == "osv-scanner":
        if not isinstance(payload, dict) or "results" not in payload:
            raise ValueError("Invalid OSV report")
        result = []
        for source in payload["results"]:
            for package in source.get("packages", []):
                name = package.get("package", {}).get("name", "unknown")
                version = package.get("package", {}).get("version", "")
                for vuln in package.get("vulnerabilities", []):
                    aliases = sorted(vuln.get("aliases", []))
                    canonical = next((a for a in aliases if a.startswith("CVE-")), vuln["id"])
                    result.append(finding(tool, vuln["id"], source.get("source", {}).get("path"), None,
                        f"{canonical} in {name}@{version}", "medium", kind=f"dependency:{canonical}:{name}"))
        return result
    if tool == "trivy":
        if not isinstance(payload, dict) or "SchemaVersion" not in payload:
            raise ValueError("Invalid Trivy report")
        result = []
        for target in payload.get("Results", []):
            for item in target.get("Vulnerabilities", []):
                identity = item["VulnerabilityID"]
                name = item.get("PkgName", "unknown")
                result.append(finding(tool, identity, target.get("Target"), None,
                    f"{identity} in {name}@{item.get('InstalledVersion', '')}", item.get("Severity", "MEDIUM").lower(),
                    kind=f"dependency:{identity}:{name}"))
            for item in target.get("Misconfigurations", []):
                if item.get("Status", "FAIL") != "FAIL":
                    continue
                result.append(finding(tool, item["ID"], target.get("Target"), item.get("CauseMetadata", {}).get("StartLine"),
                    item.get("Title", item["ID"]), item.get("Severity", "MEDIUM").lower()))
        return result
    raise ValueError("Unsupported scanner")


def source_languages(root: Path) -> list[str]:
    from services.sandbox import EXCLUDED
    extensions = {p.suffix.lower() for p in root.rglob("*") if p.is_file() and not any(part in EXCLUDED for part in p.relative_to(root).parts)}
    return (["python"] if ".py" in extensions else []) + (["javascript"] if extensions & {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"} else [])


def run_analyzer(tool: str, root: Path, *, research: bool = False, image_override: str | None = None):
    image = image_override or os.getenv("TRACEGUARD_" + tool.upper().replace("-", "_") + "_IMAGE", IMAGES[tool])
    languages = source_languages(root)
    if tool in {"codeql", "joern"} and not languages:
        return [], SensorResult(name=tool, status="SKIPPED", detail="No supported Python or JavaScript/TypeScript source files", image=image)
    output = "/workspace/out/results.json"
    commands = {
        "semgrep": ["semgrep", "scan", "--json", "--config", "p/default", "--metrics=off", "--disable-version-check", "--output", output, "/workspace/src"],
        "codeql": ["/bin/sh", "/opt/traceguard/scan.sh", "research" if research else "initial", ",".join(languages)],
        "joern": ["/opt/joern/joern-cli/joern", "--script", "/opt/traceguard/scan.sc"],
        "gitleaks": ["gitleaks", "dir", "/workspace/src", "--redact=100", "--no-banner", "--report-format=json", "--report-path=" + output, "--exit-code=0"],
        "osv-scanner": ["/osv-scanner", "scan", "source", "--recursive", "--format=json", "--output=" + output, "/workspace/src"],
        "trivy": ["trivy", "fs", "--scanners", "vuln,misconfig", "--format=json", "--output=" + output, "--no-progress", "--cache-dir=/workspace/out/trivy-cache", "/workspace/src"],
    }
    try:
        run = run_container(image, commands[tool], root, output_file=output,
                            network=tool in {"semgrep", "osv-scanner", "trivy"},
                            memory="4g" if tool in {"codeql", "joern"} else "2g", timeout=900)
        allowed = {0, 1} if tool == "osv-scanner" else {0}
        if run.exit_code not in allowed or run.output is None:
            raise SandboxError(f"{tool} exited {run.exit_code} or did not produce a report")
        findings = normalize(tool, json.loads(run.output))
        return findings, SensorResult(name=tool, status="COMPLETED", detail="Real scanner report normalized; source languages: " + (", ".join(languages) or "dependency/configuration files"),
            finding_count=len(findings), phase="research" if research else "initial", image=run.image, duration_seconds=run.duration)
    except (SandboxError, ValueError, KeyError, TypeError) as error:
        return [], SensorResult(name=tool, status="FAILED", detail=str(error)[:1200],
            phase="research" if research else "initial", image=image)
