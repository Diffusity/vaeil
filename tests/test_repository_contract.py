"""One public repository contract, run against both SQL connection URLs."""
from datetime import date
import hashlib
import os
from urllib.parse import urlsplit, urlunsplit

import pytest

from vaeil import domain as d
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

