"""Runs real installed Docker engines against our owned small Python fixture."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services import analyzers
original=analyzers.run_container

def debug(*args,**kwargs):
    result=original(*args,**kwargs)
    if result.exit_code or result.output is None:
        print("WORKER DIAGNOSTICS",args[0],result.stdout[-3500:],flush=True)
    return result

analyzers.run_container=debug
results=[]
for tool in sys.argv[1:] or analyzers.IMAGES:
    print("START",tool,flush=True)
    findings,sensor=analyzers.run_analyzer(tool,Path("tests/fixtures/sandbox_app"),research=True)
    print(json.dumps(sensor.model_dump()),flush=True)
    print("FINDINGS",[(f.title,f.location.file) for f in findings[:6]],flush=True)
    results.append({"sensor":sensor.model_dump(),"findings":[f.model_dump() for f in findings]})
Path("storage").mkdir(exist_ok=True)
Path("storage/scanner-smoke.json").write_text(json.dumps(results,indent=2))
raise SystemExit(1 if any(r["sensor"]["status"]!="COMPLETED" for r in results) else 0)
