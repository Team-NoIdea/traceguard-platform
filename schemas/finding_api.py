"""API envelope for findings persisted with completed scan reports."""

from pydantic import BaseModel

from schemas.finding import SecurityFinding


class FindingRecord(BaseModel):
    finding: SecurityFinding
    repository: str
    branch: str
    scan_id: str
    detected_at: str | None = None
