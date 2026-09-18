"""Apply a prevalidated diff and run compile/tests in this disposable container only."""
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path("/workspace/src")
result = {"apply": False, "build": False, "tests": False, "test_exit_code": None}

def run(args, timeout=180):
    return subprocess.run(args, cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=timeout, env={**os.environ, "PYTHONPATH": str(root)})

try:
    baseline = run([sys.executable, "-m", "pytest", "-q", "--disable-warnings", "-p", "no:cacheprovider"], timeout=240)
    result["baseline_tests"] = baseline.returncode == 0
    regression = Path("/workspace/regression.py")
    result["regression_fails_before"] = False
    result["regression_passes_after"] = False
    regression_command = [sys.executable, "-m", "pytest", str(regression), "-q", "-p", "no:cacheprovider"]
    if regression.exists() and regression.stat().st_size:
        result["regression_fails_before"] = run(regression_command,timeout=90).returncode == 1
    patch = "/workspace/patch.diff"
    checked = run(["git", "apply", "--ignore-space-change", "--check", "--", patch])
    if checked.returncode == 0:
        result["apply"] = run(["git", "apply", "--ignore-space-change", "--", patch]).returncode == 0
    if result["apply"]:
        result["build"] = run([sys.executable, "-m", "compileall", "-q", "."]).returncode == 0
        if result["build"]:
            tests = run([sys.executable, "-m", "pytest", "-q", "--disable-warnings", "-p", "no:cacheprovider"], timeout=240)
            result["test_exit_code"] = tests.returncode
            result["tests"] = tests.returncode == 0
            if result["regression_fails_before"]:
                result["regression_passes_after"] = run(regression_command,timeout=90).returncode == 0
            # Exit 5 (no tests) is NOT success.
except subprocess.TimeoutExpired:
    result["error"] = "Build or tests exceeded the time limit"
finally:
    Path("/workspace/out/validation.json").write_text(json.dumps(result))
