"""Read findings only from the authenticated user's scans."""
from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import UserProfile
from schemas.finding_api import FindingRecord
from services.authentication import current_user
from services.scan_service import list_scans
from services.mongodb_service import MongoUnavailableError
router = APIRouter(prefix="/findings", tags=["findings"])

@router.get("", response_model=list[FindingRecord])
def read_findings(user: UserProfile = Depends(current_user)):
    try:
        return [FindingRecord(finding=f, repository=s.repository_url, branch=s.branch,
            scan_id=s.scan_id, detected_at=s.started_at) for s in list_scans(user.firebase_uid) for f in s.report.findings]
    except MongoUnavailableError as error:
        raise HTTPException(503, str(error)) from error
