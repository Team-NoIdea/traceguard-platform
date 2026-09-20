import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from main import app
from routes import scans
from services import pdf_report
from services.authentication import current_user
from schemas.auth import UserProfile
from schemas.scan import ScanResponse

@pytest.fixture(autouse=True)
def reset_auth():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

def sample(status="COMPLETED"):
    return ScanResponse(scan_id="owned",repository_url="https://github.com/a/b",branch="main",started_at="2026-09-20T00:00:00Z",status=status)

def client():
    app.dependency_overrides[current_user]=lambda:UserProfile(firebase_uid="alice")
    return TestClient(app)

def test_pdf_requires_identity():
    assert TestClient(app).post("/scans/owned/report.pdf").status_code==401

def test_pdf_foreign_scan_never_calls_ai(monkeypatch):
    monkeypatch.setattr(scans,"get_scan",lambda scan_id,uid:None)
    monkeypatch.setattr(pdf_report,"generate_narrative",lambda scan:pytest.fail("Unauthorized AI call"))
    assert client().post("/scans/foreign/report.pdf").status_code==404

def test_running_scan_cannot_export(monkeypatch):
    monkeypatch.setattr(scans,"get_scan",lambda *a:sample("RUNNING"))
    assert client().post("/scans/owned/report.pdf").status_code==409

def test_ai_report_download_is_pdf(monkeypatch):
    monkeypatch.setattr(scans,"get_scan",lambda sid,uid:sample() if uid=="alice" else None)
    monkeypatch.setattr(pdf_report,"generate_narrative",lambda scan:"Executive summary\nNo findings were recorded; coverage is limited.\n"*150)
    response=client().post("/scans/owned/report.pdf")
    assert response.status_code==200
    assert response.headers["content-type"]=="application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert b"%%EOF" in response.content[-30:]
    assert response.headers["cache-control"]=="no-store"

def test_ai_failure_does_not_export_fake_ai_report(monkeypatch):
    monkeypatch.setattr(scans,"get_scan",lambda *a:sample())
    def fail(scan):raise HTTPException(503,"Provider unavailable")
    monkeypatch.setattr(pdf_report,"generate_narrative",fail)
    assert client().post("/scans/owned/report.pdf").status_code==503


def test_report_has_separate_long_generation_timeout(monkeypatch):
    calls=[]
    def model(messages,**kwargs):
        calls.append(kwargs)
        return "Executive summary"
    monkeypatch.setattr(pdf_report,"ask_model",model)
    assert pdf_report.generate_narrative(sample())=="Executive summary"
    assert calls==[{"timeout":180}]
