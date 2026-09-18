"""Authentication and persisted profile contracts."""

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    firebase_uid: str
    email: str | None = None
    display_name: str | None = None
    photo_url: str | None = None
    roles: list[str] = Field(default_factory=lambda: ["user"])


class AuthMeResponse(BaseModel):
    user: UserProfile
