"""End-to-end Admin console HTTP contracts with real repository transactions."""
from datetime import timedelta
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


def test_invite_issuance_rechecks_authority_origin_and_duplicate_digest(repository_url, monkeypatch):
    with open_repository(repository_url) as repo:
        client, application = client_for(repo)
        application.seed_admin(**ADMIN)
        with client:
            assert client.post("/api/admin/invites", json={}).status_code == 401
            assert client.post("/api/sessions", json=ADMIN).status_code == 200
            assert client.post("/api/admin/invites", json={}, headers={"Origin": "https://wrong.invalid"}).status_code == 403
            assert client.post("/api/admin/invites", json={"issuer_id": "forged"}).status_code == 400
            code = "InviteSecretCanaryZXQ"
            monkeypatch.setattr(application.tokens, "new_token", lambda: code)
            assert client.post("/api/admin/invites").status_code == 201
            duplicate = client.post("/api/admin/invites")
            assert duplicate.status_code == 409 and duplicate.json() == {"reason": "invite_conflict"}
            assert code not in duplicate.text
            monkeypatch.undo()
            applied = client.post("/api/applications", json=BODY | {"invite_code": code})
            applicant_id = applied.json()["applicant_id"]
            member_login = {"email": BODY["email"], "password": BODY["password"]}
            assert client.post("/api/sessions", json=member_login).status_code == 200
            assert client.post("/api/admin/invites").status_code == 403
            assert client.post("/api/sessions", json=ADMIN).status_code == 200
            route = f"/api/admin/applications/{applicant_id}/decision"
            assert client.post(route, json={"decision": "approve"}).status_code == 204
            assert client.post("/api/sessions", json=member_login).json()["role"] == "member"
            assert client.post("/api/admin/invites").status_code == 403
            assert client.post("/api/sessions", json=ADMIN).status_code == 200
            application.clock.moment += timedelta(days=1)
            assert client.post("/api/admin/invites").status_code == 401


def test_escalation_audit_failure_rolls_back_and_concurrent_decisions_record_one(repository_url, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    import pytest
    from test_t7_application import setup, Moderator, REQUEST
    from vaeil.domain.messaging import EscalationDecision, MessageConflictError
    from vaeil.domain.repository import RepositoryError
    from vaeil.domain.vetting import Verdict

    with open_repository(repository_url) as repo:
        app, actors, _ = setup(repo, Moderator(Verdict.APPROVED))
        member, admin = actors['a'], actors['admin']
        receipt = app.send_message(actor=member, conversation_id="ab", request_id=REQUEST, text="My number is 98765.43210")
        identifier = receipt.message_id
        with repo.transaction() as unit:
            audit_id = unit.list_audit(subject_id=identifier)[0].event_id
            before = unit.list_delivered_messages("ab")
        with monkeypatch.context() as patch:
            patch.setattr(app.tokens, "new_id", lambda: audit_id)
            with pytest.raises(RepositoryError):
                app.decide_escalation(actor=admin, message_id=identifier, decision=EscalationDecision.APPROVE)
        assert [item.message_id for item in app.list_review_messages(actor=admin)] == [identifier]
        gate = Barrier(2)

        def attempt(decision):
            gate.wait(timeout=5)
            try:
                app.decide_escalation(actor=admin, message_id=identifier, decision=decision)
            except MessageConflictError:
                return None
            return decision

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = tuple(pool.map(attempt, (EscalationDecision.APPROVE, EscalationDecision.REJECT)))
        assert results.count(None) == 1
        winner = next(decision for decision in results if decision is not None)
        with repo.transaction() as unit:
            assert unit.list_delivered_messages("ab") == before
            assert [item.kind.value for item in unit.list_audit(subject_id=identifier) if item.kind.value.startswith("queue_")] == [
                "queue_approved" if winner is EscalationDecision.APPROVE else "queue_rejected"
            ]
        assert app.list_review_messages(actor=admin) == ()
