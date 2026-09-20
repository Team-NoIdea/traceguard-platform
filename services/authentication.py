"""Shared, fail-closed Firebase authentication dependency."""
import logging
from firebase_admin import auth
from fastapi import Header, HTTPException
from schemas.auth import UserProfile
from services.firebase_service import verify_id_token


logger = logging.getLogger(__name__)

def current_user(authorization: str | None = Header(default=None)) -> UserProfile:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Bearer Firebase ID token required")
    try:
        claims = verify_id_token(token.strip())
        uid = claims.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ValueError("Missing identity")
    except (auth.RevokedIdTokenError, auth.UserDisabledError, auth.UserNotFoundError) as error:
        logger.warning("Firebase session rejected: %s", type(error).__name__)
        raise HTTPException(401, "Your session is no longer valid. Please sign in again.") from error
    except (auth.InvalidIdTokenError, ValueError) as error:
        # Raw SDK messages can contain input; log only an allowlisted reason.
        reason = "issued_in_future" if "used too early" in str(error).lower() else type(error).__name__
        logger.warning("Firebase token rejected: %s", reason)
        raise HTTPException(401, "Invalid or expired Firebase ID token. Please sign in again.") from error
    except Exception as error:
        logger.error("Firebase verification unavailable: %s", type(error).__name__)
        raise HTTPException(503, "Sign-in verification is temporarily unavailable. Please try again.") from error
    return UserProfile(firebase_uid=uid, email=claims.get("email"),
                       display_name=claims.get("name"), photo_url=claims.get("picture"))
