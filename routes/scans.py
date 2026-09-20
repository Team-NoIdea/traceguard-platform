"""Authenticated, owner-scoped scan API."""
from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import UserProfile
from schemas.scan import ScanRequest, ScanResponse
from services.authentication import current_user
from services.mongodb_service import MongoUnavailableError
from services.scan_service import get_scan, list_scans, enqueue_scan
router = APIRouter(prefix="/scans", tags=["scans"])

@router.get("", response_model=list[ScanResponse])
def read_scans(user: UserProfile = Depends(current_user)):
    try:
        return list_scans(user.firebase_uid)
    except MongoUnavailableError as error:
        raise HTTPException(503, str(error)) from error

@router.get("/{scan_id}", response_model=ScanResponse)
def read_scan(scan_id: str, user: UserProfile = Depends(current_user)):
    try:
        scan = get_scan(scan_id, user.firebase_uid)
    except MongoUnavailableError as error:
        raise HTTPException(503, str(error)) from error
    if scan is None:
        raise HTTPException(404, "Scan not found")
    return scan

@router.post("/run", response_model=ScanResponse, status_code=202)
def run_scan(payload: ScanRequest, user: UserProfile = Depends(current_user)):
    try:
        return enqueue_scan(payload, user.firebase_uid)
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except MongoUnavailableError as error:
        raise HTTPException(503, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(429, str(error)) from error

from schemas.remediation import FixRequest, FixAttempt
from services.remediation_service import validate_fix

@router.post("/{scan_id}/fixes/validate", response_model=FixAttempt)
def run_fix_validation(scan_id: str, payload: FixRequest, user: UserProfile = Depends(current_user)):
    try:
        return validate_fix(scan_id, user.firebase_uid, payload)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except MongoUnavailableError as error:
        raise HTTPException(503, str(error)) from error


@router.post("/{scan_id}/report.pdf")
def download_report(scan_id: str, user: UserProfile = Depends(current_user)):
    from fastapi.responses import Response
    from services.pdf_report import export_report
    scan = read_scan(scan_id, user)
    if scan.status in {"QUEUED", "RUNNING"}:
        raise HTTPException(409, "Wait for this scan to finish before generating its report")
    content = export_report(scan)
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="traceguard-report.pdf"',
        "Cache-Control": "no-store",
    })
