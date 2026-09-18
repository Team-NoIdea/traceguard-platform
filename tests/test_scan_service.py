from pathlib import Path

from services.scan_service import _discover_python_routes


def test_discovers_fastapi_routes(tmp_path: Path):
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/users')\ndef users(): pass\n",
        encoding="utf-8",
    )

    framework, routes = _discover_python_routes(tmp_path)

    assert framework == "fastapi"
    assert [(route.method, route.path, route.function) for route in routes] == [
        ("GET", "/users", "users")
    ]
