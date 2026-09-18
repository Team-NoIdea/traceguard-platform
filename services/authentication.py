"""Shared, fail-closed Firebase authentication dependency."""
from fastapi import Header, HTTPException
from schemas.auth import UserProfile
from services.firebase_service import verify_id_token


def current_user(authorization: str | None = Header(default=None)) -> UserProfile:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Bearer Firebase ID token required")
    try:
        claims = verify_id_token(token.strip())
        uid = claims.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ValueError("Missing identity")
    except Exception as error:
        raise HTTPException(401, "Invalid or expired Firebase ID token") from error
    return UserProfile(firebase_uid=uid, email=claims.get("email"),
                       display_name=claims.get("name"), photo_url=claims.get("picture"))
