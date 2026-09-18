"""Owned local fixture: real engines, real runtime, real patch/tests/rescan; no fake findings."""
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from schemas.scan import ScanRequest
from schemas.remediation import FixRequest
from services import scan_service
from services.remediation_service import validate_fix

fixture=Path("tests/fixtures/sandbox_app").resolve()
# Replace only the network transport with a copy of our own fixture. All analyzers execute normally.
def fixture_checkout(request,target,commit=None):
    shutil.copytree(fixture,target)
    subprocess.run(["git","init",str(target)],check=True,capture_output=True)
    subprocess.run(["git","-C",str(target),"add","."],check=True,capture_output=True)
    subprocess.run(["git","-C",str(target),"-c","user.name=TraceGuard Test","-c","user.email=test@localhost","commit","-m","owned fixture"],check=True,capture_output=True,env={**os.environ,"GIT_AUTHOR_DATE":"2026-09-01T00:00:00Z","GIT_COMMITTER_DATE":"2026-09-01T00:00:00Z"})
    actual = subprocess.check_output(["git","-C",str(target),"rev-parse","HEAD"],text=True).strip()
    if commit and commit != actual:
        raise ValueError("Fixture commit changed")
    return actual
scan_service._clone=fixture_checkout
scan=scan_service.scan_repository(ScanRequest(repository_url="https://github.com/traceguard/owned-fixture",authorized=True,runtime_enabled=True),"local-fixture-test")
print("SCAN",scan.status,[(s.name,s.status,s.finding_count) for s in scan.sensors],flush=True)
original=(fixture/"main.py").read_text()
updated=original.replace("return eval(value)","return int(value)")
diff="".join(difflib.unified_diff(original.splitlines(True),updated.splitlines(True),fromfile="a/main.py",tofile="b/main.py"))
finding=next(f for f in scan.report.findings if "CWE-95" in f.cwe)
regression="import pytest\nfrom main import calculate\n\ndef test_expression_is_not_executed():\n    with pytest.raises(ValueError):\n        calculate('1 + 1')\n"
result=validate_fix(scan.scan_id,"local-fixture-test",FixRequest(finding_id=finding.finding_id,unified_diff=diff,regression_test=regression))
print("FIX",result.model_dump_json(),flush=True)
Path("storage").mkdir(exist_ok=True)
Path("storage/end-to-end-smoke.json").write_text(json.dumps({"fixture":True,"scan":scan.model_dump(),"fix":result.model_dump()},indent=2))
raise SystemExit(0 if scan.status=="COMPLETED" and result.status=="VERIFIED" else 1)
