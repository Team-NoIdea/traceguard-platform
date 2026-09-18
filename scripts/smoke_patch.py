import difflib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.sandbox import run_container
root=Path("tests/fixtures/sandbox_app")
source=(root/"main.py").read_text()
diff="".join(difflib.unified_diff(source.splitlines(True),source.replace("return eval(value)","return int(value)").splitlines(True),fromfile="a/main.py",tofile="b/main.py"))
regression="import pytest\nfrom main import calculate\n\ndef test_expression_is_not_executed():\n    with pytest.raises(ValueError):\n        calculate('1 + 1')\n"
r=run_container("traceguard/runtime:local",["python","/opt/traceguard/validate.py"],root,extra={"patch.diff":diff.encode(),"regression.py":regression.encode()},output_file="/workspace/out/validation.json")
print(r.stdout);print(r.output.decode() if r.output else "no report")
