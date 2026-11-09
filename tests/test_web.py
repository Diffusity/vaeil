"""The approved public synthetic HTTP seam; no auth or private-data input."""

from fastapi.testclient import TestClient
import pytest


def test_demo_endpoint_projects_exact_anonymous_payload():
    from vaeil.web import create_app

    with TestClient(create_app()) as client:
        response = client.get("/api/demo/member")
    assert response.status_code == 200
    assert response.json() == {
        "pseudonym": "Comet",
        "values_profile": {
            "relationship_intent": "long_term", "life_stage": "undergraduate",
            "interests": ["reading"], "values": ["honesty"],
            "communication_style": "direct", "pace_and_lifestyle": "quiet_and_routine",
            "about": "",
        },
    }


def test_health_is_real_and_missing_build_has_clear_setup_response(tmp_path, monkeypatch):
    from vaeil import web

    monkeypatch.setattr(web, "FRONTEND_DIST", tmp_path)
    with TestClient(web.create_app()) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        page = client.get("/")
    assert page.status_code == 503
    assert "npm.cmd run build --prefix frontend" in page.text


@pytest.mark.parametrize("query", ["revealed=true", "viewer_id=intruder", "subject=other", "legal_name=x"])
def test_parameters_cannot_expand_the_demo_payload(query):
    from vaeil.web import create_app

    with TestClient(create_app()) as client:
        response = client.get("/api/demo/member?" + query)
    assert response.status_code == 400
    assert "intruder" not in response.text


@pytest.mark.parametrize("path", ["/api/missing", "/api/demo/member/private", "/api/register", "/openapi.json"])
def test_unknown_api_and_registration_routes_are_not_an_spa_shell(path):
    from vaeil.web import create_app

    with TestClient(create_app()) as client:
        response = client.get(path)
    assert response.status_code == 404
    assert "text/html" not in response.headers["content-type"]


def test_http_body_and_headers_never_include_private_fixture_canaries():
    from vaeil.web import create_app

    with TestClient(create_app()) as client:
        response = client.get("/api/demo/member")
    assert response.headers["cache-control"] == "no-store"
    for canary in ("DemoPrivateNameZXQ", "demo-private-zxq@example.invalid", "+919876543210",
                   "1987-03-14", "14/03/1987", "date_of_birth", "legal_name", "email", "phone"):
        assert canary not in response.text + repr(dict(response.headers))
