"""
TraceGuard backend — FastAPI application entrypoint.

Deliberately minimal for the hackathon: no DB, no queue, no Docker
orchestration here. This process is the integration/backend layer
that will eventually sit between the security engines (Semgrep,
CodeQL, Joern, runtime fuzzing, etc.) and the frontend/API consumers.

Run locally:
    uvicorn main:app --reload

See README.md for full setup instructions.
"""

from fastapi import FastAPI

from routes import system

app = FastAPI(
    title="TraceGuard",
    description="AI-assisted application security testing platform — backend API",
    version="0.1.0",
)

app.include_router(system.router)
