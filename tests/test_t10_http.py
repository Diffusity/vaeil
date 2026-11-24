"""T10 HTTP flow over the real database and existing session authority."""
from fastapi.testclient import TestClient

from test_t6_application import app_for
from test_t7_application import setup
from test_t7_http import login
from vaeil.adapters.persistence import open_repository
from vaeil.web import create_app

pytest_plugins = ["test_repository_contract"]


def client_for(repo):
    chat, _, _ = setup(repo)
    return TestClient(create_app(admission_application=app_for(repo), message_application=chat),
                      base_url="https://testserver", headers={"Origin": "https://testserver"})


def test_admin_proposes_only_anonymous_match_and_both_must_accept(repository_url):
    with open_repository(repository_url) as repo, client_for(repo) as client:
        # A-B are active in the T7 fixture; no other pair can currently start.
        login(client, "admin")
        assert client.post("/api/admin/matches", json={}).json() == {"created": 0}
        with repo.transaction() as unit:
            from dataclasses import replace
            unit.store_conversation(replace(unit.get_conversation("ab"), revealed=True))
            unit.commit()
        assert client.post("/api/admin/matches", json={"member_id": "a"}).status_code == 400
        assert client.post("/api/admin/matches", json={}).json() == {"created": 1}
        assert client.post("/api/admin/matches", json={}).json() == {"created": 0}
        login(client, "a")
        assert client.post("/api/admin/matches", json={}).status_code == 403
        response = client.get("/api/me/matches")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        match, = response.json()["matches"]
        assert set(match) == {"match_id", "state", "decision", "partner"}
        assert set(match["partner"]) == {"pseudonym", "values_profile"}
        assert match["partner"]["pseudonym"] == "Star"
        for canary in ("PrivateCanary", "c@example.invalid", "1987-03-14", "9876543210"):
            assert canary not in response.text
        path = "/api/me/matches/" + match["match_id"] + "/decision"
        login(client, "b")
        assert client.post(path, json={"decision": "accept"}).status_code == 404
        login(client, "a")
        assert client.post(path, json={"decision": "accept"}, headers={"Origin": "https://wrong.invalid"}).status_code == 403
        first = client.post(path, json={"decision": "accept"}).json()
        assert first["state"] == "pending" and first["decision"] == "accept"
        assert "conversation_id" not in first
        login(client, "c")
        second = client.post(path, json={"decision": "accept"}).json()
        assert second["state"] == "accepted"
        conversation_id = second["conversation_id"]
        assert client.post(path, json={"decision": "accept"}).json() == second
        assert client.post(path, json={"decision": "decline"}).status_code == 409
        assert client.get(f"/api/conversations/{conversation_id}/messages").status_code == 200
        with repo.transaction() as unit:
            created = unit.get_conversation(conversation_id)
        assert created.participant_ids == ("a", "c") and not created.revealed
