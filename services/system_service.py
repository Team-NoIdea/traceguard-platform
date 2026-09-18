"""
Business logic for system-level endpoints.

Trivial for now, but keeping it out of routes/ means that once real
checks are needed here (e.g. "is Semgrep reachable?", "is the mock
data loaded?") they can be added in one place without touching the
route/controller layer.
"""

SERVICE_NAME = "TraceGuard"
SERVICE_VERSION = "0.1.0"


def get_service_info() -> dict:
    """Return basic identification info for the running service."""
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "version": SERVICE_VERSION,
    }


def get_health_status() -> dict:
    """Return liveness status. Extend with real checks as needed."""
    return {"status": "healthy"}
