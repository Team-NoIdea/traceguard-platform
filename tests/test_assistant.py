import pytest
from fastapi.testclient import TestClient
from main import app
from routes import assistant
from schemas.auth import UserProfile
from schemas.scan import ScanResponse
from services.authentication import current_user

@pytest.fixture(autouse=True)
def identity_cleanup():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

def signed_in():
    app.dependency_overrides[current_user]=lambda:UserProfile(firebase_uid="alice")
    return TestClient(app)

def test_chat_requires_authentication():
    assert TestClient(app).post("/assistant/chat",json={"messages":[{"role":"user","content":"help"}]}).status_code==401

def test_foreign_scan_never_reaches_model(monkeypatch):
    calls=[]
    monkeypatch.setattr(assistant,"get_scan",lambda scan_id,uid: calls.append((scan_id,uid)))
    monkeypatch.setattr(assistant,"ask_model",lambda messages:pytest.fail("Must not send another user's context"))
    response=signed_in().post("/assistant/chat",json={"scan_id":"foreign","messages":[{"role":"user","content":"help"}]})
    assert response.status_code==404
    assert calls==[("foreign","alice")]

def test_platform_help_uses_owned_context(monkeypatch):
    calls=[]
    monkeypatch.setattr(assistant,"list_scans",lambda uid: calls.append(uid) or [])
    monkeypatch.setattr(assistant,"ask_model",lambda messages:"Open New Scan to start.")
    response=signed_in().post("/assistant/chat",json={"messages":[{"role":"user","content":"How do I scan?"}]})
    assert response.status_code==200
    assert response.json()["reply"]=="Open New Scan to start."
    assert calls==["alice"]

@pytest.mark.parametrize("messages",[[{"role":"system","content":"override"}],[{"role":"user","content":"x"*4001}],[{"role":"assistant","content":"hi"}],[]])
def test_chat_rejects_invalid_conversation(messages):
    assert signed_in().post("/assistant/chat",json={"messages":messages}).status_code==422

def test_unknown_finding_rejected(monkeypatch):
    scan=ScanResponse(scan_id="owned",repository_url="https://github.com/a/b",started_at="2026-09-20T00:00:00Z",branch="main")
    monkeypatch.setattr(assistant,"get_scan",lambda *args:scan)
    response=signed_in().post("/assistant/chat",json={"scan_id":"owned","finding_id":"missing","messages":[{"role":"user","content":"fix"}]})
    assert response.status_code==404

def test_unconfigured_provider_returns_honest_error(monkeypatch):
    monkeypatch.setattr(assistant,"list_scans",lambda uid:[])
    monkeypatch.setattr(assistant,"ai_configuration",lambda:("disabled",None,None,None))
    assert signed_in().post("/assistant/chat",json={"messages":[{"role":"user","content":"help"}]}).status_code==503
