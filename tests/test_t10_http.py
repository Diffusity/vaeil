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



def test_declined_pair_is_never_proposed_again_and_incomplete_member_is_skipped(repository_url):
    from test_repository_contract import example_member
    from vaeil.domain.authentication import PrincipalRecord, Role, AdmissionStatus
    from vaeil.domain.privacy import PrivateText

    with open_repository(repository_url) as repo, client_for(repo) as client:
        with repo.transaction() as unit:
            from dataclasses import replace
            unit.store_conversation(replace(unit.get_conversation("ab"), blocked=True))
            identity = example_member("00-draft").identity
            unit.add_principal(PrincipalRecord(identity, identity.email, PrivateText("test-only:fiction password"),
                                               Role.MEMBER, AdmissionStatus.APPROVED))
            unit.commit()
        login(client, "admin")
        assert client.post("/api/admin/matches", json={}).json() == {"created": 1}
        login(client, "a")
        match, = client.get("/api/me/matches").json()["matches"]
        assert match["partner"]["pseudonym"] == "Star"
        path = "/api/me/matches/" + match["match_id"] + "/decision"
        first = client.post(path, json={"decision": "decline"}).json()
        assert first["state"] == "declined" and "conversation_id" not in first
        assert client.post(path, json={"decision": "decline"}).json() == first
        login(client, "c")
        assert client.post(path, json={"decision": "accept"}).status_code == 409
        login(client, "admin")
        assert client.post("/api/admin/matches", json={}).json() == {"created": 1}
        login(client, "c")
        current = client.get("/api/me/matches").json()["matches"]
        assert {(item["state"], item["partner"]["pseudonym"]) for item in current} == {
            ("declined", "Comet"), ("pending", "Orbit"),
        }


def test_concurrent_batches_and_retried_accepts_create_only_one_match_and_conversation(repository_url, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from threading import Barrier
    import pytest
    from vaeil.adapters.persistence import SqlUnitOfWork
    from vaeil.application.matching import MatchingApplication
    from vaeil.domain.matching import MatchDecision
    from vaeil.domain.repository import RepositoryError

    def compete(left, right):
        gate = Barrier(2)

        def run(action):
            gate.wait(timeout=10)
            return action()

        with ThreadPoolExecutor(max_workers=2) as workers:
            return tuple(workers.map(run, (left, right)))

    with open_repository(repository_url) as repo:
        chat, actors, _ = setup(repo)
        matching = MatchingApplication(repo, tokens=chat.tokens)
        with repo.transaction() as unit:
            unit.store_conversation(replace(unit.get_conversation("ab"), revealed=True))
            unit.commit()

        def propose():
            return matching.propose_matches(actor=actors["admin"])

        assert sorted(compete(propose, propose)) == [0, 1]
        pending, = matching.read_matches(actor=actors["a"])

        def accept(who):
            return matching.decide_match(actor=actors[who], match_id=pending.match_id,
                                         decision=MatchDecision.ACCEPT)

        assert accept("a").conversation_id is None

        def fail_write(unit, match):
            assert unit.get_conversation(match.conversation_id).participant_ids == ("a", "c")
            raise RepositoryError("Simulated Match write failure.")

        with monkeypatch.context() as patch:
            patch.setattr(SqlUnitOfWork, "update_match", fail_write)
            with pytest.raises(RepositoryError):
                accept("c")
        current, = matching.read_matches(actor=actors["c"])
        assert current.state == "pending" and current.decision is None and current.conversation_id is None
        with repo.transaction() as unit:
            assert [item.conversation_id for item in unit.list_conversations()] == ["ab"]

        first, retry = compete(lambda: accept("c"), lambda: accept("c"))
        assert first == retry and first.conversation_id
        with repo.transaction() as unit:
            assert {item.conversation_id for item in unit.list_conversations()} == {"ab", first.conversation_id}



def test_stale_slot_does_not_record_acceptance_and_pair_can_retry(repository_url):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from threading import Barrier
    import pytest
    from vaeil.application.matching import MatchingApplication
    from vaeil.domain.conversation import Conversation
    from vaeil.domain.matching import MatchConflictError, MatchDecision

    with open_repository(repository_url) as repo:
        chat, actors, _ = setup(repo)
        matching = MatchingApplication(repo, tokens=chat.tokens)
        with repo.transaction() as unit:
            unit.store_conversation(replace(unit.get_conversation("ab"), revealed=True))
            unit.commit()
        assert matching.propose_matches(actor=actors["admin"]) == 1
        pending, = matching.read_matches(actor=actors["a"])
        with repo.transaction() as unit:
            competing = Conversation("other-active", ("b", "c"))
            unit.store_conversation(competing)
            unit.commit()

        def accept(who):
            return matching.decide_match(actor=actors[who], match_id=pending.match_id,
                                         decision=MatchDecision.ACCEPT)

        first = accept("a")
        assert first.state == "pending"
        with pytest.raises(MatchConflictError):
            accept("c")
        current, = matching.read_matches(actor=actors["c"])
        assert current.decision is None and current.conversation_id is None
        with repo.transaction() as unit:
            unit.store_conversation(replace(competing, revealed=True))
            unit.commit()

        # In the clean separate B-C history, the later A-C acceptance can safely be retried.
        gate = Barrier(2)

        def attempt(who):
            gate.wait(timeout=10)
            return accept(who)

        with ThreadPoolExecutor(max_workers=2) as workers:
            replies = tuple(workers.map(attempt, ("a", "c")))
        final, = matching.read_matches(actor=actors["a"])
        assert final.state == "accepted"
        assert {reply.conversation_id for reply in replies} - {None} == {final.conversation_id}
        with repo.transaction() as unit:
            assert {item.conversation_id for item in unit.list_conversations()} == {
                "ab", "other-active", final.conversation_id,
            }


def test_simultaneous_distinct_members_accept_one_new_conversation(repository_url):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from threading import Barrier
    from vaeil.application.matching import MatchingApplication
    from vaeil.domain.matching import MatchDecision

    with open_repository(repository_url) as repo:
        chat, actors, _ = setup(repo)
        matching = MatchingApplication(repo, tokens=chat.tokens)
        with repo.transaction() as unit:
            unit.store_conversation(replace(unit.get_conversation("ab"), revealed=True))
            unit.commit()
        assert matching.propose_matches(actor=actors["admin"]) == 1
        pending, = matching.read_matches(actor=actors["a"])
        gate = Barrier(2)

        def accept(who):
            gate.wait(timeout=10)
            return matching.decide_match(actor=actors[who], match_id=pending.match_id,
                                         decision=MatchDecision.ACCEPT)

        with ThreadPoolExecutor(max_workers=2) as workers:
            replies = tuple(workers.map(accept, ("a", "c")))
        assert sorted(reply.state for reply in replies) == ["accepted", "pending"]
        accepted = next(reply for reply in replies if reply.state == "accepted")
        assert accepted.conversation_id
        with repo.transaction() as unit:
            assert {item.conversation_id for item in unit.list_conversations()} == {"ab", accepted.conversation_id}
