"""TraceGuard API: authenticated scans, evidence correlation, and isolated fix validation."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import (
    auth,
    assistant,
    correlation,
    correlation_routes,
    findings,
    scans,
    system,
    workflow,
)

app = FastAPI(
    title="TraceGuard",
    description="AI-assisted application security testing platform — backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "TRACEGUARD_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(correlation.router)
app.include_router(workflow.router)
app.include_router(correlation_routes.router)
app.include_router(scans.router)
app.include_router(auth.router)
app.include_router(findings.router)

app.include_router(assistant.router)
