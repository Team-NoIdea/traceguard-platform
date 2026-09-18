"""Firebase-authenticated profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError
from schemas.auth import AuthMeResponse, UserProfile
from services.authentication import current_user
from services.mongodb_service import upsert_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=AuthMeResponse)
def read_me(user: UserProfile = Depends(current_user)) -> AuthMeResponse:
    try:
        upsert_user(user.model_dump())
    except PyMongoError as error:
        raise HTTPException(503, "Profile store unavailable") from error
    return AuthMeResponse(user=user)
