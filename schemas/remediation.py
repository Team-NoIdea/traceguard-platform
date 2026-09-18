from typing import Literal
from pydantic import BaseModel, Field

class FixRequest(BaseModel):
    finding_id: str
    unified_diff: str | None = Field(default=None, max_length=50000)
    regression_test: str | None = Field(default=None, max_length=20000)

class FixAttempt(BaseModel):
    fix_id: str
    finding_id: str
    status: Literal["RUNNING", "VERIFIED", "FAILED", "NOT_VERIFIED"] = "RUNNING"
    commit_sha: str
    unified_diff: str
    checks: dict[str, bool] = Field(default_factory=dict)
    details: list[str] = Field(default_factory=list)
    sensors: list[dict] = Field(default_factory=list)
