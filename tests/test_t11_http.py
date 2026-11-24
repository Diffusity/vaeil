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



def test_competing_block_and_reveal_preserve_only_committed_history(repository_url):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from test_t8_application import reveal_setup
    from vaeil.application.safety import SafetyApplication
    from vaeil.domain.reveal import RevealBlockedError
    from vaeil.domain.repository import AuditKind
    from vaeil.domain.safety import ReportReason

    with open_repository(repository_url) as repo:
        reveal, messages, actors, clock = reveal_setup(repo)
        a, b = actors["a"], actors["b"]
        safety = SafetyApplication(repo, tokens=messages.tokens, clock=clock)
        reveal.set_reveal_consent(actor=a, conversation_id="ab", consent=True)
        gate = Barrier(2)

        def block():
            gate.wait(timeout=10)
            return safety.block_conversation(actor=a, conversation_id="ab")

        def complete():
            gate.wait(timeout=10)
            try:
                return reveal.set_reveal_consent(actor=b, conversation_id="ab", consent=True).revealed
            except RevealBlockedError:
                return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            blocked = pool.submit(block)
            completed = pool.submit(complete)
            assert blocked.result().blocked
            revealed = completed.result()
        a_report = safety.submit_report(actor=a, conversation_id="ab", reason=ReportReason.OTHER)
        b_report = safety.submit_report(actor=b, conversation_id="ab", reason=ReportReason.HARASSMENT)
        assert a_report.report_id != b_report.report_id
        with repo.transaction() as unit:
            final = unit.get_conversation("ab")
            kinds = [item.kind for item in unit.list_audit(subject_id="ab")]
        assert final.blocked and final.revealed is revealed and not final.active
        assert kinds.count(AuditKind.CONVERSATION_BLOCKED) == 1
        assert kinds.count(AuditKind.CONVERSATION_REVEALED) == int(revealed)


def test_block_and_reports_roll_back_on_audit_failure_and_serialize_retries(repository_url, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    import pytest
    from vaeil.adapters.persistence import SqlUnitOfWork
    from vaeil.application.matching import MatchingApplication
    from vaeil.application.safety import SafetyApplication
    from vaeil.domain.messaging import MessageBlockedError, MessageReviewDecision
    from vaeil.domain.repository import RepositoryError
    from vaeil.domain.safety import ReportConflictError, ReportDecision, ReportReason

    with open_repository(repository_url) as repo:
        messages, actors, clock = setup(repo)
        a, b, admin = actors["a"], actors["b"], actors["admin"]
        safety = SafetyApplication(repo, tokens=messages.tokens, clock=clock)
        sent = messages.send_message(actor=a, conversation_id="ab", request_id=REQUEST, text="PendingCanary")
        messages.submit_for_review(actor=a, message_id=sent.message_id)

        def blocked(who):
            return safety.block_conversation(actor=who, conversation_id="ab")

        def report():
            return safety.submit_report(actor=a, conversation_id="ab", reason=ReportReason.SCAM)

        def fail_audit(_unit, _event):
            raise RepositoryError("Fixture audit unavailable.")

        def race(left, right):
            barrier = Barrier(2)

            def run(action):
                barrier.wait(timeout=10)
                return action()

            with ThreadPoolExecutor(max_workers=2) as pool:
                return tuple(pool.map(run, (left, right)))

        with monkeypatch.context() as patch:
            patch.setattr(SqlUnitOfWork, "append_audit", fail_audit)
            with pytest.raises(RepositoryError):
                blocked(a)
            with pytest.raises(RepositoryError):
                report()
        with repo.transaction() as unit:
            assert not unit.get_conversation("ab").blocked
        assert not safety.pending_reports(actor=admin)

        assert all(item.blocked for item in race(lambda: blocked(a), lambda: blocked(b)))
        with pytest.raises(MessageBlockedError):
            messages.decide_message(actor=admin, message_id=sent.message_id, decision=MessageReviewDecision.RELEASE)
        assert messages.read_conversation(actor=b, conversation_id="ab").blocked
        first, same = race(report, report)
        assert first == same

        def decide(decision):
            return safety.decide_report(actor=admin, report_id=first.report_id, decision=decision)

        with monkeypatch.context() as patch:
            patch.setattr(SqlUnitOfWork, "append_audit", fail_audit)
            with pytest.raises(RepositoryError):
                decide(ReportDecision.REJECT)
        assert safety.pending_reports(actor=admin) == (first,)

        def attempt(decision):
            try:
                decide(decision)
            except ReportConflictError:
                return False
            return True

        assert sorted(race(lambda: attempt(ReportDecision.REJECT), lambda: attempt(ReportDecision.APPROVE))) == [False, True]
        with repo.transaction() as unit:
            assert [event.kind.value for event in unit.list_audit(subject_id="ab")] == ["conversation_blocked"]
            kinds = [event.kind.value for event in unit.list_audit(subject_id=first.report_id)]
            assert kinds.count("report_submitted") == 1
            assert sum(k in {"report_rejected", "report_approved"} for k in kinds) == 1

        matching = MatchingApplication(repo, tokens=messages.tokens)
        assert matching.propose_matches(actor=admin) == 1
        proposal, = matching.read_matches(actor=a)
        assert proposal.partner.pseudonym.value == "Star"
