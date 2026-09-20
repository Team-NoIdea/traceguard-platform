"""Bounded baseline/mutation requests executed inside the networkless target container."""
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib import request, error, parse

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

opener = request.build_opener(NoRedirect, request.ProxyHandler({}))

def get(path):
    started = time.monotonic()
    try:
        with opener.open("http://127.0.0.1:18765" + path, timeout=2) as response:
            return response.status, "traceback" in response.read(4096).decode("utf-8", "replace").lower(), round(time.monotonic()-started,3)
    except error.HTTPError as response:
        return response.code, "traceback" in response.read(4096).decode("utf-8", "replace").lower(), round(time.monotonic()-started,3)
    except (OSError, ValueError):
        return None, False, round(time.monotonic()-started,3)

def main():
    config = json.loads(Path("/workspace/request.json").read_text())
    entry = config["entrypoint"]
    if config["framework"] != "vite" and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*", entry):
        raise ValueError("Invalid entrypoint")
    if config["framework"] == "vite":
        subprocess.run(["node", "node_modules/vite/bin/vite.js", "build"], check=True, timeout=180)
        command = ["node", "node_modules/vite/bin/vite.js", "preview", "--host", "127.0.0.1", "--port", "18765", "--strictPort"]
    elif config["framework"] == "flask":
        command = [sys.executable, "-m", "flask", "--app", entry, "run", "--host", "127.0.0.1", "--port", "18765"]
    else:
        command = [sys.executable, "-m", "uvicorn", entry, "--host", "127.0.0.1", "--port", "18765", "--no-access-log"]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    observations = []
    try:
        for _ in range(50):
            if process.poll() is not None:
                raise RuntimeError("Target failed to start; check entrypoint and worker dependencies")
            if get("/")[0] is not None:
                break
            time.sleep(.2)
        else:
            raise RuntimeError("Target readiness timed out")
        for route in config["routes"][:10]:
            if route["method"] != "GET":
                continue
            path = route["path"]
            if not path.startswith("/") or path.startswith("//") or any(c in path for c in "{}<>?#\\"):
                continue
            baseline = get(path)
            observations.append({"route": route, "experiment": "baseline", "baseline": baseline, "observed": baseline})
            if config.get("mutate") and baseline[0] is not None and baseline[0] < 400:
                # One harmless query input at a time; no destructive exploit payloads.
                for key, value in [("id", ""), ("id", "not-a-number"), ("limit", "-1"), ("q", "x" * 256)]:
                    time.sleep(.15)
                    observed = get(path + "?" + parse.urlencode({key:value}))
                    observations.append({"route":route,"experiment":key+"="+value[:30],"baseline":baseline,"observed":observed})
                    if observed[0] is None:
                        break
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
    Path("/workspace/out/runtime.json").write_text(json.dumps({"observations": observations}))

if __name__ == "__main__":
    main()
