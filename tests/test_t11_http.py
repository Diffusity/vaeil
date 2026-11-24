"""T11 HTTP contracts over real serialized repositories."""
from fastapi.testclient import TestClient
from test_t6_application import app_for
from test_t7_application import setup, Moderator, REQUEST
from test_t7_http import login
from vaeil.adapters.persistence import open_repository
from vaeil.domain.vetting import Verdict
from vaeil.web import create_app

pytest_plugins = ["test_repository_contract"]
ORIGIN = "https://testserver"


def client_for(repo):
    messages, actors, clock = setup(repo, Moderator(Verdict.APPROVED))
    from vaeil.application.reveal import RevealApplication

    admission = app_for(repo)
    return TestClient(create_app(admission_application=admission, message_application=messages,
                      reveal_application=RevealApplication(repo, tokens=messages.tokens, clock=clock)),
                      base_url=ORIGIN, headers={"Origin": ORIGIN}), actors, clock


def test_participant_blocks_chat_and_can_still_report(repository_url):
    with open_repository(repository_url) as repo:
        client, _, _ = client_for(repo)
        with client:
            prefix = "/api/conversations/ab"
            login(client, "a")
            assert client.post(prefix + "/messages", json={"request_id": REQUEST, "text": "DeliveryCanaryZXQ"}).status_code == 202
            assert client.post(prefix + "/block", json={"actor_id": "b"}).status_code == 400
            assert client.post(prefix + "/block", headers={"Origin": "https://wrong.invalid"}).status_code == 403
            login(client, "c")
            assert client.post(prefix + "/block").json() == {"reason": "not_found"}
            assert client.post(prefix + "/reports", json={"reason": "scam"}).status_code == 404
            login(client, "b")
            result = client.post(prefix + "/block")
            assert result.status_code == 200 and result.json() == {"conversation_id": "ab", "blocked": True}
            assert result.headers["cache-control"] == "no-store"
            login(client, "a")
            assert client.post(prefix + "/block").json() == result.json()
            closed = client.get(prefix + "/messages")
            assert closed.json() == {"conversation_id": "ab", "blocked": True, "delivered": [], "attempts": []}
            assert "DeliveryCanaryZXQ" not in closed.text
            assert client.get(prefix + "/partner").status_code == 409
            assert client.post(prefix + "/messages", json={"request_id": REQUEST, "text": "No retry"}).status_code == 409
            assert client.post(prefix + "/reports", json={"reason": "scam", "target": "b"}).status_code == 400
            receipt = client.post(prefix + "/reports", json={"reason": "scam"})
            assert receipt.status_code == 201 and set(receipt.json()) == {"report_id"}
            assert client.post(prefix + "/reports", json={"reason": "scam"}).json() == receipt.json()
            assert client.post(prefix + "/reports", json={"reason": "other"}).status_code == 409
            assert client.get("/api/admin/reports").status_code == 403
            login(client, "admin")
            queue = client.get("/api/admin/reports")
            row, = queue.json()["reports"]
            assert set(row) == {"report_id", "conversation_id", "reason", "created_at", "status"}
            assert row["report_id"] == receipt.json()["report_id"] and row["reason"] == "scam" and row["status"] == "pending"
            decision = "/api/admin/reports/" + row["report_id"] + "/decision"
            assert client.post(decision, json={"decision": "approve"}).status_code == 204
            assert client.post(decision, json={"decision": "approve"}).status_code == 204
            assert client.post(decision, json={"decision": "reject"}).status_code == 409
            assert client.get("/api/admin/reports").json() == {"reports": []}
        with repo.transaction() as unit:
            assert [event.kind.value for event in unit.list_audit(subject_id="ab")] == ["conversation_blocked"]
            events = unit.list_audit(subject_id=row["report_id"])
            assert {event.kind.value: event.actor_id for event in events} == {"report_submitted": "a", "report_approved": "admin"}
            assert "DeliveryCanaryZXQ" not in repr(events) + queue.text
