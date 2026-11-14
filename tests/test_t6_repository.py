"""T6 extends the same disposable SQLite/PostgreSQL repository contract."""
from datetime import date
import pytest
from vaeil.domain import MemberIdentity
from vaeil.domain.privacy import PrivateText
from vaeil.adapters.persistence import open_repository

pytest_plugins = ["test_repository_contract"]


def principal(identifier="p1", email="fiction@example.invalid"):
    from vaeil.domain.authentication import PrincipalRecord, Role, AdmissionStatus
    return PrincipalRecord(MemberIdentity(identifier, "PrivateCanary", email, None, date(1987, 3, 14)),
                           PrivateText(email), PrivateText("EncodedHashCanary"), Role.APPLICANT, AdmissionStatus.NEEDS_REVIEW)


def test_principal_and_application_roundtrip_without_private_diagnostics(repository_url):
    from vaeil.domain.authentication import ApplicationRecord
    from vaeil.domain.admission import validate_application_note
    record = principal()
    note = validate_application_note("I seek a thoughtful long term relationship.", owner=record.identity)
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            unit.add_application(ApplicationRecord(record, note))
            unit.commit()
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            loaded = unit.get_principal_by_email("fiction@example.invalid")
            assert loaded == record
            assert unit.get_application("p1").note == note
            assert unit.list_pending_applications() == (ApplicationRecord(record, note),)
            assert "PrivateCanary" not in repr(loaded) and "EncodedHashCanary" not in repr(loaded)
            assert "1987" not in str(loaded)
            assert unit.get_principal("missing") is None


@pytest.mark.parametrize("other_email", ["fiction@example.invalid", " FICTION@example.invalid ", "ｆｉｃｔｉｏｎ＠example.invalid"],
                         ids=["exact", "trim-case", "nfkc"])
def test_principal_email_ownership_and_rollback(repository_url, other_email):
    from vaeil.domain.authentication import ApplicationRecord
    from vaeil.domain.repository import RepositoryError
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            unit.add_application(ApplicationRecord(principal(), "I seek a thoughtful long term relationship."))
        with repo.transaction() as unit:
            assert unit.get_principal("p1") is None
        with repo.transaction() as unit:
            unit.add_application(ApplicationRecord(principal(), "I seek a thoughtful long term relationship."))
            unit.commit()
        with pytest.raises(RepositoryError):
            with repo.transaction() as unit:
                unit.add_application(ApplicationRecord(principal("p2", other_email), "I seek a thoughtful long term relationship."))
                unit.commit()
        with repo.transaction() as unit:
            assert unit.get_principal("p2") is None


def test_invite_consumption_is_atomic_and_retry_safe(repository_url):
    from vaeil.domain import InviteAlreadyRedeemedError, InvalidInviteError
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            unit.issue_invite("fictional-invite", issuer_id="admin")
            unit.commit()
        with repo.transaction() as unit:
            unit.consume_invite("fictional-invite", principal_id="p1")
        with repo.transaction() as unit:
            unit.consume_invite("fictional-invite", principal_id="p2")
            unit.commit()
        with pytest.raises(InviteAlreadyRedeemedError):
            with repo.transaction() as unit:
                unit.consume_invite("fictional-invite", principal_id="p3")
        with pytest.raises(InvalidInviteError):
            with repo.transaction() as unit:
                unit.consume_invite("unknown", principal_id="p3")


def test_admission_is_terminal_and_rollback_preserves_queue(repository_url):
    from vaeil.domain.authentication import ApplicationRecord, AdmissionDecision, AdmissionStatus, AdmissionConflictError
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            unit.add_application(ApplicationRecord(principal(), "I seek a thoughtful long term relationship."))
            unit.commit()
        with repo.transaction() as unit:
            unit.set_admission_decision("p1", AdmissionDecision.APPROVE)
        with repo.transaction() as unit:
            assert unit.get_principal("p1").admission is AdmissionStatus.NEEDS_REVIEW
            unit.set_admission_decision("p1", AdmissionDecision.APPROVE)
            unit.commit()
        with repo.transaction() as unit:
            assert unit.get_principal("p1").admission is AdmissionStatus.APPROVED
            assert unit.list_pending_applications() == ()
        with pytest.raises(AdmissionConflictError):
            with repo.transaction() as unit:
                unit.set_admission_decision("p1", AdmissionDecision.REJECT)


def test_remote_postgres_uses_verified_tls_even_if_url_requests_disable(monkeypatch):
    import psycopg
    from pathlib import Path
    from vaeil.domain.repository import RepositoryError
    connections = []
    def refuse_connection(*args, **kwargs):
        connections.append(kwargs)
        raise psycopg.OperationalError("Synthetic connection refusal.")
    monkeypatch.setattr(psycopg, "connect", refuse_connection)
    with pytest.raises(RepositoryError):
        with open_repository("postgresql://fiction:fiction@db.example.invalid/fiction?sslmode=disable"):
            pass
    assert len(connections) == 1
    assert connections[0]["sslmode"] == "verify-full"
    assert connections[0]["connect_timeout"] == 2
    assert "statement_timeout=2000" in connections[0]["options"]
    assert "lock_timeout=2000" in connections[0]["options"]
    assert Path(connections[0]["sslrootcert"]).is_file()
