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

