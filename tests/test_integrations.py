import json
import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.auth import UserProfile
from schemas.scan import ScanResponse
from schemas.correlation import CorrelationRequest
from schemas.finding import SecurityFinding
from services.authentication import current_user
from services.analyzers import normalize
from services.langgraph_pipeline import run_workflow
from services.remediation_service import validate_patch
from services import scan_service, mongodb_service

@pytest.fixture(autouse=True)
def no_external_services(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("AI_PROVIDER", "disabled")
    monkeypatch.setenv("MONGODB_URI", "")
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    scan_service.SCAN_STORE.clear()

@pytest.mark.parametrize("method,path",[("get","/scans"),("get","/scans/other"),("get","/findings"),("post","/scans/run"),("post","/correlation/report"),("post","/correlation/workflow"),("post","/scans/other/fixes/validate")])
def test_routes_require_identity(method,path):
    response = getattr(TestClient(app),method)(path)
    assert response.status_code == 401

def test_owner_cannot_read_another_users_scan():
    scan = ScanResponse(scan_id="owned", repository_url="https://github.com/a/b",branch="main",started_at="2026-09-20T00:00:00Z")
    scan_service._save(scan,"alice")
    app.dependency_overrides[current_user] = lambda:UserProfile(firebase_uid="bob")
    client=TestClient(app)
    assert client.get("/scans").json()==[]
    assert client.get("/scans/owned").status_code==404
    assert client.get("/findings").json()==[]
    app.dependency_overrides[current_user] = lambda:UserProfile(firebase_uid="alice")
    assert client.get("/scans/owned").status_code==200

def test_persistence_queries_include_owner(monkeypatch):
    queries=[]
    class Collection:
        def find_one(self,q,p): queries.append(q); return None
        def find(self,q,p): queries.append(q); return self
        def sort(self,*a): return []
    monkeypatch.setattr(mongodb_service,"_database",lambda:{"scans":Collection()})
    mongodb_service.get_scan("id","alice")
    mongodb_service.list_scans("alice")
    assert queries==[{"scan_id":"id","firebase_uid":"alice"},{"firebase_uid":"alice"}]

def test_semgrep_uses_top_level_file_and_redacts_secrets():
    result=normalize("semgrep",{"results":[{"check_id":"unsafe-eval","path":"/workspace/src/main.py","start":{"line":7},"extra":{"message":"unsafe eval","severity":"ERROR","metadata":{"cwe":["CWE-95"]}}}]})
    assert result[0].location.file=="main.py"
    assert result[0].severity=="high"
    leaks=normalize("gitleaks",[{"RuleID":"aws-key","File":"config.py","StartLine":1,"Secret":"sensitive-token","Match":"sensitive-token"}])
    assert "sensitive-token" not in leaks[0].model_dump_json()

def test_malformed_scanner_report_is_not_clean():
    for name,payload in [("codeql",{}),("semgrep",{"results":[],"errors":[{"message":"parse failure"}]}),("trivy",{})]:
        with pytest.raises(ValueError): normalize(name,payload)

def test_research_collects_new_findings():
    calls=[]
    def collect(feedback,round_number):
        calls.append((feedback,round_number))
        return [SecurityFinding(finding_id="fresh",title="New evidence",type="CWE-95",severity="high")]
    report=run_workflow(CorrelationRequest(research_again=True,feedback=["Run deep analyzers"],max_research_rounds=1),researcher=collect)
    assert len(calls)==1
    assert report.findings[0].finding_id=="fresh"
    assert any("acquired 1 scanner observations" in t for t in report.workflow_trace)

GOOD="--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-return eval(value)\n+return int(value)\n"

def test_patch_scope():
    validate_patch(GOOD,"main.py")
    for target in ["../outside.py","/absolute.py","tests/test_app.py",".github/main.py","test_app.py"]:
        with pytest.raises(ValueError): validate_patch(GOOD,target)
    with pytest.raises(ValueError): validate_patch(GOOD+"--- a/other.py\n+++ b/other.py\n", "main.py")

@pytest.mark.parametrize("url",["http://github.com/a/b","https://user@github.com/a/b","https://github.com/a/b?x=1","https://localhost/a/b","https://github.com/a/b/extra"])
def test_repository_scope(url):
    with pytest.raises(ValueError): scan_service._validate_repository_url(url)


def test_missing_findings_do_not_prove_a_fix():
    from services.correlation_service import build_report, validate_rescan
    finding=SecurityFinding(finding_id="one",title="Issue",type="CWE-95",severity="high")
    report=build_report(CorrelationRequest(findings=[finding]))
    assert validate_rescan(report,[])[0].status=="NOT_RESCANNED"

def test_input_size_limit_is_enforced(tmp_path,monkeypatch):
    from services import sandbox
    (tmp_path/"large.py").write_text("x"*100)
    monkeypatch.setattr(sandbox,"MAX_SOURCE_BYTES",50)
    with pytest.raises(sandbox.SandboxError): sandbox.source_archive(tmp_path)


@pytest.mark.parametrize("failure,status", [(ValueError("secret-token"),401), (RuntimeError("private-config"),503)])
def test_auth_failure_classification_does_not_expose_secrets(monkeypatch,caplog,failure,status):
    import services.authentication as authentication
    def reject(token):
        raise failure
    monkeypatch.setattr(authentication,"verify_id_token",reject)
    response=TestClient(app).get("/auth/me",headers={"Authorization":"Bearer secret-token"})
    assert response.status_code==status
    assert "secret-token" not in response.text+caplog.text
    assert "private-config" not in response.text+caplog.text


def test_firebase_verification_keeps_revocation_with_bounded_clock_tolerance(monkeypatch):
    from services import firebase_service
    calls=[]
    monkeypatch.setattr(firebase_service.firebase_admin,"_apps",{"test":object()})
    def verify(token,**kwargs):
        calls.append((token,kwargs))
        return {"uid":"alice"}
    monkeypatch.setattr(firebase_service.auth,"verify_id_token",verify)
    assert firebase_service.verify_id_token("test-token")=={"uid":"alice"}
    assert calls==[("test-token",{"check_revoked":True,"clock_skew_seconds":10})]


def test_javascript_scanner_selection_ignores_dependencies(tmp_path,monkeypatch):
    from services import analyzers
    from services.sandbox import RunResult
    (tmp_path/"app.tsx").write_text("export const App = () => null")
    (tmp_path/"node_modules").mkdir()
    (tmp_path/"node_modules/helper.py").write_text("pass")
    calls=[]
    def run(image,command,root,**kwargs):
        calls.append(command)
        return RunResult(0,"",b'{"runs":[]}',image,1)
    monkeypatch.setattr(analyzers,"run_container",run)
    assert analyzers.source_languages(tmp_path)==["javascript"]
    _,sensor=analyzers.run_analyzer("codeql",tmp_path)
    assert sensor.status=="COMPLETED"
    assert calls[0][-1]=="javascript"


def test_dependency_preparation_is_separate_from_networkless_execution(tmp_path,monkeypatch):
    from services import sandbox
    from subprocess import CompletedProcess
    calls=[]
    def docker(args,**kwargs):
        calls.append(args)
        data=b""
        if args[:2]==["image","inspect"]: data=b"sha256:test"
        if args[0]=="inspect": data=b'{"ExitCode":0,"OOMKilled":false}'
        return CompletedProcess(args,0,stdout=data)
    monkeypatch.setattr(sandbox,"docker",docker)
    result=sandbox.run_container("test/image",["python3","probe.py"],tmp_path,prepare_command=["npm","ci","--ignore-scripts"])
    creates=[c for c in calls if c[0]=="create"]
    assert len(creates)==2
    assert creates[0][creates[0].index("--network")+1]=="bridge"
    assert creates[1][creates[1].index("--network")+1]=="none"
    assert "--ignore-scripts" in creates[0]
    assert "--read-only" in creates[1]
    assert result.exit_code==0


def test_ai_source_context_supports_javascript_without_reading_secrets(tmp_path):
    from services.remediation_service import source_context
    from schemas.finding import Location
    (tmp_path/"app.jsx").write_text("export const App = () => null")
    (tmp_path/".env").write_text("SECRET=not-for-model")
    finding=SecurityFinding(finding_id="js",title="Issue",type="CWE-79",severity="medium",location=Location(file="app.jsx"),source_tools=["codeql"])
    assert "export const App" in source_context(tmp_path,finding)
    finding.location=Location(file=".env")
    assert source_context(tmp_path,finding)==""
    finding.location=Location(file="app.jsx")
    finding.source_tools=["gitleaks"]
    assert source_context(tmp_path,finding)==""
