"""End-to-end Admin console HTTP contracts with real repository transactions."""
from test_t6_http import BODY, client_for
from vaeil.adapters.persistence import open_repository

pytest_plugins = ["test_repository_contract"]
ADMIN = {"email": "admin@example.invalid", "password": "admin fiction password"}


def test_admin_issues_single_use_invite_then_approves_application(repository_url, caplog):
    with open_repository(repository_url) as repo:
        client, application = client_for(repo)
        application.seed_admin(**ADMIN)
        with client:
            assert client.post("/api/sessions", json=ADMIN).status_code == 200
            issuance = client.post("/api/admin/invites", json={})
            assert issuance.status_code == 201
            assert issuance.headers["cache-control"] == "no-store"
            assert set(issuance.json()) == {"invite_code"}
            code = issuance.json()["invite_code"]
            registration = BODY | {"invite_code": code}
            assert client.post("/api/applications", json=registration | {"date_of_birth": "2016-01-01"}).json() == {"reason": "age_gate"}
            applied = client.post("/api/applications", json=registration)
            assert applied.status_code == 202
            applicant_id = applied.json()["applicant_id"]
            assert applied.json()["admission"] == "NeedsReview"
            queue = client.get("/api/admin/applications")
            assert queue.json() == {"applications": [{"applicant_id": applicant_id, "application_note": registration["application_note"]}]}
            decision = client.post(f"/api/admin/applications/{applicant_id}/decision", json={"decision": "approve"})
            assert decision.status_code == 204
            assert client.get("/api/admin/applications").json() == {"applications": []}
            reuse = client.post("/api/applications", json=registration | {"email": "other@example.invalid"})
            assert reuse.status_code == 409 and reuse.json() == {"reason": "invite_used"}
        with repo.transaction() as unit:
            events = unit.list_audit(subject_id=applicant_id)
        approvals = [event for event in events if event.kind.value == "admission_approved"]
        assert len(approvals) == 1 and approvals[0].actor_id == "admin"
        assert code not in applied.text + queue.text + decision.text + reuse.text + repr(events) + caplog.text


def test_escalation_decision_is_audited_once_without_retracting_delivery(repository_url):
    from test_t7_http import client_for as chat_client, login, REQUEST
    from test_t7_application import Moderator
    from vaeil.domain.vetting import Verdict

    with open_repository(repository_url) as repo:
        with chat_client(repo, Moderator(Verdict.APPROVED)) as client:
            login(client, "a")
            text = "My number is 98765.43210"
            sent = client.post("/api/conversations/ab/messages", json={"request_id": REQUEST, "text": text})
            assert sent.status_code == 202 and sent.json()["outcome"] == "Escalated"
            identifier = sent.json()["message_id"]
            route = f"/api/admin/messages/{identifier}/escalation-decision"
            assert client.post(route, json={"decision": "reject"}).status_code == 403
            login(client, "admin")
            assert [item["message_id"] for item in client.get("/api/admin/messages").json()["messages"]] == [identifier]
            assert client.post(route, json={"decision": "reject"}).status_code == 204
            assert client.post(route, json={"decision": "reject"}).status_code == 204
            assert client.post(route, json={"decision": "approve"}).status_code == 409
            assert client.get("/api/admin/messages").json() == {"messages": []}
            login(client, "b")
            delivered = client.get("/api/conversations/ab/messages").json()["delivered"]
            assert [(item["message_id"], item["text"]) for item in delivered] == [(identifier, text)]
        with repo.transaction() as unit:
            entries = unit.list_audit(subject_id=identifier)
        assert [item.actor_id for item in entries if item.kind.value == "queue_rejected"] == ["admin"]
        assert not any(item.kind.value == "queue_approved" for item in entries)
