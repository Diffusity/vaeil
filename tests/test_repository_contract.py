"""One public repository contract, run against both SQL connection URLs."""
from datetime import date
import hashlib
import os
from urllib.parse import urlsplit, urlunsplit

import pytest

from vaeil import domain as d
from vaeil.domain import conversation as c
from vaeil.domain.privacy import PrivateText, PrivateDate


@pytest.fixture(params=["sqlite", "postgres"])
def repository_url(request, tmp_path):
    if request.param == "sqlite":
        yield "sqlite:///" + (tmp_path / "contract.sqlite").as_posix()
        return
    base = os.environ.get("VAEIL_TEST_POSTGRES_URL")
    if not base:
        pytest.skip("Disposable local PostgreSQL is supplied by contract CI")
    parsed = urlsplit(base)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        pytest.fail("Contract tests require disposable loopback PostgreSQL, never production")
    import psycopg
    from psycopg import sql

    database = "contract_" + hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:20]
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    try:
        yield urlunsplit(parsed._replace(path="/" + database))
    finally:
        with psycopg.connect(base, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))


def example_member(member_id="one", pseudonym="Comet"):
    identity = d.MemberIdentity(member_id, "PrivateCanaryZXQ", "privatecanaryzxq@example.invalid",
                                "+919876543210", date(1987, 3, 14))
    profile = d.build_values_profile(
        owner=identity, relationship_intent=d.RelationshipIntent.LONG_TERM,
        life_stage=d.LifeStage.UNDERGRADUATE, interests=[d.Interest.READING],
        values=[d.CoreValue.HONESTY], communication_style=d.CommunicationStyle.DIRECT,
        pace_and_lifestyle=d.PaceAndLifestyle.QUIET_AND_ROUTINE, about="",
    )
    return d.Member(identity, d.Pseudonym(pseudonym), profile)


def test_member_round_trip_survives_new_repository_with_wrappers(repository_url, caplog):
    from vaeil.adapters.persistence import open_repository

    original = example_member()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.add_member(original)
            transaction.commit()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            restored = transaction.get_member("one")
    assert restored == original
    assert isinstance(restored.identity.legal_name, PrivateText)
    assert isinstance(restored.identity.date_of_birth, PrivateDate)
    assert isinstance(restored.values_profile.interests, frozenset)
    for canary in ("PrivateCanaryZXQ", "privatecanaryzxq@example.invalid", "+919876543210", "1987-03-14"):
        assert canary not in repr(restored) + str(restored) + caplog.text



@pytest.mark.parametrize("equivalent", ["cOmEt", "Ｃomet", " Comet "])
def test_normalized_pseudonym_has_one_durable_owner(repository_url, equivalent):
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.commit()
        with pytest.raises(d.PseudonymTakenError):
            with repository.transaction() as transaction:
                transaction.add_member(example_member("two", equivalent))
                transaction.commit()
        with repository.transaction() as transaction:
            transaction.add_member(example_member("two", "Aurora"))
            transaction.commit()
        with pytest.raises(d.PseudonymAlreadySetError):
            with repository.transaction() as transaction:
                transaction.add_member(example_member("two", "Nebula"))
                transaction.commit()
        with repository.transaction() as transaction:
            assert transaction.get_member("two").pseudonym == d.Pseudonym("Aurora")


@pytest.mark.parametrize("candidate", ["ab", "1comet", "co.met", "admin", "x1234567890", "PrivateCanaryZXQstar"])
def test_storage_reuses_pseudonym_format_reserved_identifier_and_self_name_rules(repository_url, candidate):
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        with pytest.raises(d.InvalidPseudonymError):
            with repository.transaction() as transaction:
                transaction.add_member(example_member(pseudonym=candidate))
                transaction.commit()


def test_concurrent_normalized_claims_commit_exactly_one_owner(repository_url):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url):
        pass
    ready = Barrier(2)

    def claim(pair):
        member_id, name = pair
        with open_repository(repository_url) as repository:
            ready.wait(timeout=10)
            try:
                with repository.transaction() as transaction:
                    transaction.add_member(example_member(member_id, name))
                    transaction.commit()
                return "saved"
            except d.PseudonymTakenError:
                return "taken"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, [("one", "Comet"), ("two", "ＣOMET")]))
    assert sorted(results) == ["saved", "taken"]


def seed_participants(repository):
    with repository.transaction() as transaction:
        for member_id, name in [("one", "Comet"), ("two", "Aurora"), ("three", "Nebula")]:
            transaction.add_member(example_member(member_id, name))
        transaction.commit()


def test_conversation_projection_round_trip_stays_pair_scoped(repository_url):
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        seed_participants(repository)
        with repository.transaction() as transaction:
            transaction.store_conversation(c.Conversation("ab", ("one", "two"), revealed=True))
            transaction.store_conversation(c.Conversation("ac", ("one", "three")))
            transaction.commit()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            member = transaction.get_member("one")
            ab = transaction.get_conversation("ab")
            ac = transaction.get_conversation("ac")
    assert isinstance(d.project_member_for_viewer(member, viewer_id="two", conversation=ab.reveal_state()), d.RevealedMemberView)
    assert isinstance(d.project_member_for_viewer(member, viewer_id="three", conversation=ac.reveal_state()), d.PreRevealMemberView)
    assert ac.active and ab.open_for_chat and not ab.active


@pytest.mark.parametrize("previous,candidate", [
    (c.Conversation("ab", ("one", "two"), revealed=True), c.Conversation("ab", ("one", "two"))),
    (c.Conversation("ab", ("one", "two"), blocked=True), c.Conversation("ab", ("one", "two"))),
    (c.Conversation("ab", ("one", "two")), c.Conversation("ab", ("one", "three"))),
], ids=["reveal-regression", "block-regression", "participant-change"])
def test_durable_conversation_refuses_reversal_or_reassignment(repository_url, previous, candidate):
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        seed_participants(repository)
        with repository.transaction() as transaction:
            transaction.store_conversation(previous)
            transaction.commit()
        with pytest.raises(c.InvalidConversationTransitionError):
            with repository.transaction() as transaction:
                transaction.store_conversation(candidate)
                transaction.commit()
        with repository.transaction() as transaction:
            assert transaction.get_conversation("ab") == previous


def test_durable_block_frees_slot_but_excludes_the_pair(repository_url):
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        seed_participants(repository)
        with repository.transaction() as transaction:
            transaction.store_conversation(c.Conversation("ab", ("one", "two"), blocked=True))
            transaction.commit()
        with pytest.raises(c.PairBlockedError):
            with repository.transaction() as transaction:
                transaction.store_conversation(c.Conversation("ab-new", ("two", "one")))
        with repository.transaction() as transaction:
            transaction.store_conversation(c.Conversation("ac", ("one", "three")))
            transaction.commit()


def test_concurrent_active_conversation_opens_have_one_winner(repository_url):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        seed_participants(repository)
    ready = Barrier(2)

    def store(conversation):
        with open_repository(repository_url) as repository:
            ready.wait(timeout=10)
            try:
                with repository.transaction() as transaction:
                    transaction.store_conversation(conversation)
                    transaction.commit()
                return "saved"
            except c.MemberAlreadyActiveError:
                return "active-conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(store, [c.Conversation("ab", ("one", "two")), c.Conversation("ac", ("one", "three"))]))
    assert sorted(results) == ["active-conflict", "saved"]


def test_concurrent_stale_reveal_and_block_cannot_reverse_state(repository_url):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        seed_participants(repository)
        with repository.transaction() as transaction:
            transaction.store_conversation(c.Conversation("ab", ("one", "two")))
            transaction.commit()
    ready = Barrier(2)

    def store(conversation):
        with open_repository(repository_url) as repository:
            ready.wait(timeout=10)
            try:
                with repository.transaction() as transaction:
                    transaction.store_conversation(conversation)
                    transaction.commit()
                return "saved"
            except c.InvalidConversationTransitionError:
                return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(store, [c.Conversation("ab", ("one", "two"), revealed=True),
                                       c.Conversation("ab", ("one", "two"), blocked=True)]))
    assert sorted(results) == ["saved", "stale"]



def audit_event(event_id="event-one", **changes):
    from datetime import datetime, timezone
    from vaeil.domain.repository import AuditEvent, AuditKind

    fields = dict(event_id=event_id, occurred_at=datetime(2026, 11, 1, 12, tzinfo=timezone.utc),
                  actor_id="admin-one", subject_id="one", kind=AuditKind.ADMISSION_APPROVED,
                  reason_codes=())
    fields.update(changes)
    return AuditEvent(**fields)


def test_domain_and_audit_commit_or_rollback_together(repository_url):
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import MemberNotFoundError

    event = audit_event()
    with open_repository(repository_url) as repository:
        with pytest.raises(RuntimeError):
            with repository.transaction() as transaction:
                transaction.add_member(example_member())
                transaction.append_audit(event)
                raise RuntimeError("synthetic abort")
        with repository.transaction() as transaction:
            assert transaction.list_audit(subject_id="one") == ()
            with pytest.raises(MemberNotFoundError):
                transaction.get_member("one")
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.append_audit(event)
            transaction.commit()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            assert transaction.get_member("one") == example_member()
            assert transaction.list_audit(subject_id="one") == (event,)


def test_context_exit_without_commit_leaves_no_domain_or_audit_write(repository_url):
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import MemberNotFoundError

    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.append_audit(audit_event())
        with repository.transaction() as transaction:
            assert transaction.list_audit(subject_id="one") == ()
            with pytest.raises(MemberNotFoundError):
                transaction.get_member("one")


def test_constraint_failure_rolls_back_earlier_domain_and_audit_writes(repository_url):
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import MemberNotFoundError

    with open_repository(repository_url) as repository:
        with pytest.raises(d.PseudonymTakenError):
            with repository.transaction() as transaction:
                transaction.add_member(example_member())
                transaction.append_audit(audit_event())
                transaction.add_member(example_member("two", "COMET"))
                transaction.commit()
        with repository.transaction() as transaction:
            assert transaction.list_audit(subject_id="one") == ()
            with pytest.raises(MemberNotFoundError):
                transaction.get_member("one")


@pytest.mark.parametrize("operation", ["UPDATE audit_events SET actor_id = 'changed'", "DELETE FROM audit_events"])
def test_database_refuses_audit_update_and_delete(repository_url, operation):
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError
    from vaeil.adapters.persistence import open_repository

    event = audit_event()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.append_audit(event)
            transaction.commit()
        engine = create_engine(repository_url.replace("postgresql://", "postgresql+psycopg://"), hide_parameters=True)
        try:
            with pytest.raises(DBAPIError):
                with engine.begin() as connection:
                    connection.execute(text(operation))
        finally:
            engine.dispose()
        with repository.transaction() as transaction:
            assert transaction.list_audit(subject_id="one") == (event,)
            assert not hasattr(transaction, "update_audit") and not hasattr(transaction, "delete_audit")


def test_duplicate_audit_id_never_replaces_the_original(repository_url):
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import AuditKind, RepositoryError

    original = audit_event()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.append_audit(original)
            transaction.commit()
        with pytest.raises(RepositoryError):
            with repository.transaction() as transaction:
                transaction.append_audit(audit_event(kind=AuditKind.ADMISSION_REJECTED))
                transaction.commit()
        with repository.transaction() as transaction:
            assert transaction.list_audit(subject_id="one") == (original,)


def test_audit_shape_refuses_arbitrary_private_payload_and_pins_required_decisions():
    from dataclasses import fields
    from vaeil.domain.repository import AuditEvent, AuditKind

    assert {field.name for field in fields(AuditEvent)} == {
        "event_id", "occurred_at", "actor_id", "subject_id", "kind", "reason_codes"
    }
    assert {kind.value for kind in AuditKind} >= {
        "invite_redeemed", "vetting_approved", "vetting_needs_review", "identifier_escalated",
        "conversation_revealed", "conversation_blocked", "report_submitted",
        "admission_approved", "admission_rejected", "queue_approved", "queue_rejected",
        "message_released", "message_discarded",
    }
    with pytest.raises(TypeError):
        audit_event(reason_codes=("privatecanaryzxq@example.invalid",))


def stored_session():
    from datetime import datetime, timezone
    from vaeil.domain.repository import StoredSession

    return StoredSession("a" * 64, "account-one", datetime(2026, 12, 5, 12, tzinfo=timezone.utc))


def test_server_session_is_durable_explicit_and_deletable(repository_url):
    from vaeil.adapters.persistence import open_repository

    session = stored_session()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.put_session(session)
            transaction.commit()
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            restored = transaction.get_session("a" * 64)
            assert restored == session
            assert isinstance(restored.token_digest, PrivateText)
            assert "a" * 64 not in repr(restored)
            assert transaction.get_session("b" * 64) is None
        with repository.transaction() as transaction:
            transaction.delete_session("a" * 64)
            transaction.commit()
        with repository.transaction() as transaction:
            assert transaction.get_session("a" * 64) is None


def test_session_write_rolls_back_without_commit(repository_url):
    from vaeil.adapters.persistence import open_repository

    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.put_session(stored_session())
        with repository.transaction() as transaction:
            assert transaction.get_session("a" * 64) is None


def test_session_is_frozen_slotted_and_refuses_generic_export():
    from dataclasses import FrozenInstanceError, asdict
    import pickle
    from vaeil.domain.privacy import PrivateSerializationError

    session = stored_session()
    assert not hasattr(session, "__dict__")
    with pytest.raises(FrozenInstanceError):
        session.principal_id = "changed"
    for export in (asdict, pickle.dumps):
        with pytest.raises(PrivateSerializationError) as error:
            export(session)
        assert "a" * 64 not in str(error.value)


def test_malformed_connection_configuration_has_safe_error_and_traceback():
    import traceback
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import RepositoryError

    canary = "PrivateConfigurationCanary"
    with pytest.raises(RepositoryError) as error:
        with open_repository("postgresql://user:password@localhost:" + canary + "/database"):
            pytest.fail("Invalid configuration must not open a repository")
    assert canary not in str(error.value) + "".join(traceback.format_exception(error.value))


def test_sql_logging_never_copies_private_parameters(repository_url, caplog):
    import logging
    from vaeil.adapters.persistence import open_repository

    caplog.set_level(logging.INFO, logger="sqlalchemy.engine.Engine")
    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.put_session(stored_session())
            transaction.commit()
    for canary in ("PrivateCanaryZXQ", "privatecanaryzxq@example.invalid", "+919876543210", "1987-03-14", "a" * 64):
        assert canary not in caplog.text


def test_failed_transaction_cannot_commit_even_if_caller_catches_the_error(repository_url):
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import MemberNotFoundError, RepositoryError

    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.append_audit(audit_event())
            with pytest.raises(d.PseudonymTakenError):
                transaction.add_member(example_member("two", "COMET"))
            with pytest.raises(RepositoryError):
                transaction.commit()
        with repository.transaction() as transaction:
            assert transaction.list_audit(subject_id="one") == ()
            with pytest.raises(MemberNotFoundError):
                transaction.get_member("one")


def test_committed_unit_of_work_cannot_start_an_unlocked_second_transaction(repository_url):
    from vaeil.adapters.persistence import open_repository
    from vaeil.domain.repository import RepositoryError

    with open_repository(repository_url) as repository:
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.commit()
            with pytest.raises(RepositoryError):
                transaction.add_member(example_member("two", "Aurora"))


def test_default_repository_url_is_local_sqlite_without_database_install(tmp_path, monkeypatch):
    from vaeil.adapters.persistence import open_repository

    monkeypatch.chdir(tmp_path)
    with open_repository() as repository:
        with repository.transaction() as transaction:
            transaction.add_member(example_member())
            transaction.commit()
    with open_repository() as repository:
        with repository.transaction() as transaction:
            assert transaction.get_member("one") == example_member()
