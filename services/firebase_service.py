"""Firebase ID-token verification with signature and revocation checks."""

from __future__ import annotations

import os
import base64
import json
from typing import Any

try:
    import firebase_admin
    from firebase_admin import auth, credentials
except ImportError:  # pragma: no cover
    firebase_admin = None
    auth = credentials = None


def verify_id_token(token: str) -> dict[str, Any]:
    if not token:
        raise ValueError("Missing Firebase ID token")
    if firebase_admin is None:
        raise RuntimeError("firebase-admin is not installed")
    if not firebase_admin._apps:
        credential_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        credential_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_B64")
        if credential_b64:
            service_account = json.loads(
                base64.b64decode(credential_b64).decode("utf-8")
            )
            firebase_admin.initialize_app(credentials.Certificate(service_account))
        elif credential_path:
            firebase_admin.initialize_app(credentials.Certificate(credential_path))
        else:
            firebase_admin.initialize_app()
    # Allow small host/container clock differences from Firebase issuance time.
    return auth.verify_id_token(token, check_revoked=True, clock_skew_seconds=10)
