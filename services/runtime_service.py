"""Translate isolated runtime observations into evidence without inventing baselines."""
import hashlib
import json
import os
from pathlib import Path
from schemas.finding import SecurityFinding, RuntimeEvidence, Location
from schemas.scan import SensorResult
from services.sandbox import run_container, SandboxError

def runtime_probe(root, framework, routes, entrypoint="main:app", mutate=False):
    if framework not in {"fastapi", "flask", "vite"}:
        return [], SensorResult(name="runtime", status="SKIPPED", detail="No supported Flask/FastAPI or root Vite application detected")
    image = os.getenv("TRACEGUARD_NODE_RUNTIME_IMAGE", "traceguard/node-runtime:local") if framework == "vite" else os.getenv("TRACEGUARD_RUNTIME_IMAGE", "traceguard/runtime:local")
    prepare = ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--cache=/workspace/out/npm-cache"] if framework == "vite" else None
    config = {"entrypoint":entrypoint, "framework":framework, "routes":[r.model_dump() for r in routes], "mutate":mutate}
    try:
        run = run_container(image, ["python3", "/opt/traceguard/probe.py"], root,
            extra={"request.json": json.dumps(config).encode()}, output_file="/workspace/out/runtime.json", timeout=360, prepare_command=prepare)
        if run.exit_code or run.output is None:
            raise SandboxError("Runtime failed to start or probe; configure the entrypoint/dependencies")
        observations = json.loads(run.output)["observations"]
        findings = []
        for item in observations:
            status, traceback, elapsed = item["observed"]
            baseline = item["baseline"][0]
            anomaly = status is None or status >= 500 or traceback or elapsed > max(1, item["baseline"][2]*5)
            if not anomaly:
                continue
            route = item["route"]
            identity = route["path"] + "|" + item["experiment"]
            description = f"{item['experiment']}: baseline HTTP {baseline}, observed HTTP {status}, latency {elapsed}s, traceback={traceback}"
            findings.append(SecurityFinding(
                finding_id="runtime-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
                title="Runtime anomaly at " + route["path"], type="runtime_anomaly", severity="medium",
                location=Location(file=route.get("file") or "unknown", line=route.get("line"), function=route.get("function")),
                runtime_evidence=[RuntimeEvidence(endpoint=route["path"], method="GET", baseline_status=baseline,
                    mutated_status=status, function=route.get("function"), evidence=description, type="runtime_anomaly")],
                source_tools=["runtime"], status="NEEDS_REVIEW"))
        return findings, SensorResult(name="runtime", status="COMPLETED", finding_count=len(findings),
            detail=f"{len(observations)} bounded HTTP observations in networkless Docker sandbox" + ("; Vite production build passed (not browser interaction coverage)" if framework == "vite" else ""), image=run.image,
            duration_seconds=run.duration, phase="research" if mutate else "initial")
    except (SandboxError, KeyError, ValueError, TypeError) as error:
        return [], SensorResult(name="runtime", status="FAILED", detail=str(error), image=image,
            phase="research" if mutate else "initial")
