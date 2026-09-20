import json
import subprocess
import sys
from pathlib import Path
languages = sys.argv[2].split(",") if len(sys.argv) > 2 else ["python"]
runs = []
for language in languages:
    if language not in {"python", "javascript"}:
        raise ValueError("Unsupported CodeQL language")
    version = {"python":"1.8.10", "javascript":"2.4.5"}[language]
    database = f"/workspace/out/codeql-{language}"
    subprocess.run(["codeql", "database", "create", database, "--language="+language, "--source-root=/workspace/src", "--threads=2", "--ram=2048"], check=True)
    suite = f"/opt/codeql-packs/codeql/{language}-queries/{version}/codeql-suites/{language}-security-and-quality.qls"
    output = f"/workspace/out/{language}.sarif"
    subprocess.run(["codeql", "database", "analyze", database, suite, "--search-path=/opt/codeql-packs", "--format=sarif-latest", "--output="+output, "--threads=2", "--ram=2048"], check=True)
    runs.extend(json.loads(Path(output).read_text())["runs"])
Path("/workspace/out/results.json").write_text(json.dumps({"version":"2.1.0", "runs":runs}))
