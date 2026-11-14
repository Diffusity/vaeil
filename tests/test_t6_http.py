"""HTTP authorization and explicit payloads over the approved application seam."""
from fastapi.testclient import TestClient
import pytest
from test_t6_application import app_for, issue, CapturingModel
from vaeil.domain import Verdict
from vaeil.adapters.persistence import open_repository

pytest_plugins = ["test_repository_contract"]
ORIGIN = "https://testserver"
BODY = dict(legal_name="LegalCanaryZXQ", email="emailcanary@example.invalid", phone="+919876543210",
            date_of_birth="1987-03-14", invite_code="invite-one", password="fiction password",
            application_note="I seek a thoughtful long term relationship.")
PRIVATE = (BODY["legal_name"], BODY["email"], BODY["phone"], BODY["date_of_birth"], BODY["invite_code"], BODY["password"])


def client_for(repo, model=None):
    from vaeil.web import create_app
    application = app_for(repo, model)
    return TestClient(create_app(admission_application=application), base_url=ORIGIN, headers={"Origin": ORIGIN}), application


def test_registration_login_cookie_restricted_profile_and_logout(repository_url, caplog):
    with open_repository(repository_url) as repo:
        issue(repo)
        client, _ = client_for(repo)
        with client:
            applied = client.post("/api/applications", json=BODY)
            assert applied.status_code == 202 and applied.json()["admission"] == "NeedsReview"
            login = client.post("/api/sessions", json={"email": BODY["email"], "password": BODY["password"]})
            assert login.status_code == 200
            cookie = login.headers["set-cookie"]
            assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Secure" in cookie and "Path=/" in cookie
            assert client.get("/api/session").json()["role"] == "applicant"
            assert client.get("/api/me/profile").status_code == 403
            assert client.delete("/api/session").status_code == 204
            assert client.get("/api/session").status_code == 401
            responses = applied.text + login.text + caplog.text
            for canary in PRIVATE:
                assert canary not in responses
            assert "synthetic-token" not in applied.text + login.text


@pytest.mark.parametrize("extra", [{"role": "admin"}, {"revealed": True}, {"actor_id": "admin"}])
def test_registration_cannot_supply_authority(repository_url, extra):
    with open_repository(repository_url) as repo:
        issue(repo)
        client, _ = client_for(repo)
        with client:
            assert client.post("/api/applications", json=BODY | extra).status_code == 400


@pytest.mark.parametrize("bad_body", [None, [], {"legal_name": "EchoCanary"}, BODY | {"date_of_birth": "InvalidDobCanary"}])
def test_invalid_request_errors_never_echo_inputs(repository_url, bad_body, caplog):
    with open_repository(repository_url) as repo:
        client, _ = client_for(repo)
        with client:
            response = client.post("/api/applications", json=bad_body)
        assert response.status_code == 400
        assert "EchoCanary" not in response.text + caplog.text and "InvalidDobCanary" not in response.text + caplog.text
        for canary in PRIVATE:
            assert canary not in response.text + caplog.text


def test_csrf_cross_origin_and_absent_origin_are_refused(repository_url):
    with open_repository(repository_url) as repo:
        issue(repo)
        client, _ = client_for(repo)
        with client:
            for origin in ("https://evil.invalid", "null", ""):
                response = client.post("/api/applications", json=BODY, headers={"Origin": origin})
                assert response.status_code == 403
            assert client.post("/api/applications", json=BODY).status_code == 202


def test_admin_note_only_queue_decision_and_own_identity_projection(repository_url):
    from test_t6_profiles import fields
    with open_repository(repository_url) as repo:
        issue(repo)
        client, application = client_for(repo)
        application.seed_admin(email="admin@example.invalid", password="admin fiction password")
        with client:
            response = client.post("/api/applications", json=BODY)
            applicant_id = response.json()["applicant_id"]
            client.post("/api/sessions", json={"email": BODY["email"], "password": BODY["password"]})
            assert client.get("/api/admin/applications").status_code == 403
            client.post("/api/sessions", json={"email": "admin@example.invalid", "password": "admin fiction password"})
            queue = client.get("/api/admin/applications")
            assert queue.json() == {"applications": [{"applicant_id": applicant_id, "application_note": BODY["application_note"]}]}
            for canary in PRIVATE:
                assert canary not in queue.text
            assert client.post(f"/api/admin/applications/{applicant_id}/decision", json={"decision": "approve"}).status_code == 204
            client.post("/api/sessions", json={"email": BODY["email"], "password": BODY["password"]})
            saved = client.put("/api/me/profile", json={"pseudonym": "Comet"} | fields())
            assert saved.status_code == 200
            own = client.get("/api/me/profile")
            assert own.json()["legal_name"] == BODY["legal_name"] and own.json()["email"] == BODY["email"]
            assert own.json()["date_of_birth"] == BODY["date_of_birth"]
            assert "application_note" not in own.text and BODY["application_note"] not in own.text
            assert own.headers["cache-control"] == "no-store"


def test_test_only_approved_fake_does_not_create_an_http_model_switch(repository_url):
    with open_repository(repository_url) as repo:
        issue(repo)
        client, _ = client_for(repo, CapturingModel(Verdict.APPROVED))
        with client:
            assert client.post("/api/applications", json=BODY | {"model": "approve"}).status_code == 400
