"""Application seam with real transactions, fixed time and injected external ports."""
from datetime import date, datetime, timedelta, timezone
import pytest
from vaeil.adapters.persistence import open_repository
from vaeil.domain import MemberIdentity, Verdict, UnderageError
from vaeil.domain.privacy import PrivateText
from vaeil.domain.authentication import Role, AdmissionStatus, AdmissionDecision, AccessDeniedError, AuthenticationError

pytest_plugins = ["test_repository_contract"]
NOTE = "I seek a thoughtful long term relationship."


class FixedClock:
    moment = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
    def today(self):
        return self.moment.date()
    def now(self):
        return self.moment


class Passwords:
    def hash_password(self, raw):
        return PrivateText("test-only:" + raw)
    def verify_password(self, raw, encoded):
        return encoded == PrivateText("test-only:" + raw)


class Tokens:
    count = 0
    def new_token(self):
        self.count += 1
        return "synthetic-token-" + str(self.count)
    def new_id(self):
        self.count += 1
        return "synthetic-event-" + str(self.count)


class CapturingModel:
    def __init__(self, result=Verdict.NEEDS_REVIEW):
        self.result = result
        self.received = []
    def vet(self, note):
        self.received.append(note)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def command(identifier="one", invite="invite-one", dob=date(1987, 3, 14), note=NOTE):
    from vaeil.application.admission import ApplicationSubmission
    return ApplicationSubmission(MemberIdentity(identifier, "PrivateCanary", identifier + "@example.invalid", None, dob),
                                 invite, note, Passwords().hash_password("fiction password"))


def app_for(repo, model=None):
    from vaeil.application.admission import AdmissionApplication
    return AdmissionApplication(repo, passwords=Passwords(), tokens=Tokens(), clock=FixedClock(),
                                model=CapturingModel() if model is None else model)


def issue(repo):
    with repo.transaction() as unit:
        unit.issue_invite("invite-one", issuer_id="admin")
        unit.commit()


def test_pending_login_is_restricted_then_admin_approval_is_audited(repository_url):
    with open_repository(repository_url) as repo:
        issue(repo)
        model = CapturingModel()
        app = app_for(repo, model)
        app.seed_admin(email="admin@example.invalid", password="admin fiction password")
        receipt = app.apply(command())
        assert receipt.admission is AdmissionStatus.NEEDS_REVIEW
        assert model.received == [NOTE]
        grant = app.login(" ONE@example.invalid ", "fiction password")
        actor = app.session(grant.token)
        assert actor.role is Role.APPLICANT
        assert grant.expires_at == FixedClock.moment + timedelta(hours=24)
        assert "synthetic-token" not in repr(grant) + str(grant)
        with pytest.raises(AccessDeniedError):
            app.decide_admission(actor=actor, applicant_id="one", decision=AdmissionDecision.APPROVE)
        admin = app.session(app.login("admin@example.invalid", "admin fiction password").token)
        queue = app.pending_applications(actor=admin)
        assert [(item.principal.identity.member_id, item.note) for item in queue] == [("one", NOTE)]
        app.decide_admission(actor=admin, applicant_id="one", decision=AdmissionDecision.APPROVE)
        assert app.session(grant.token).role is Role.MEMBER
        with repo.transaction() as unit:
            kinds = [item.kind.value for item in unit.list_audit(subject_id="one")]
            assert "invite_redeemed" in kinds and "vetting_needs_review" in kinds and "admission_approved" in kinds
            assert "PrivateCanary" not in repr(unit.list_audit(subject_id="one"))


@pytest.mark.parametrize("email,password", [("unknown@example.invalid", "fiction password"), ("one@example.invalid", "incorrect password")])
def test_wrong_credentials_have_identical_safe_failure(repository_url, email, password):
    with open_repository(repository_url) as repo:
        issue(repo)
        app = app_for(repo)
        app.apply(command())
        with pytest.raises(AuthenticationError) as result:
            app.login(email, password)
        assert str(result.value) == "Invalid credentials."


def test_session_boundary_logout_and_unknown_token(repository_url):
    with open_repository(repository_url) as repo:
        issue(repo)
        app = app_for(repo)
        app.apply(command())
        grant = app.login("one@example.invalid", "fiction password")
        app.clock.moment = grant.expires_at - timedelta(microseconds=1)
        assert app.session(grant.token).principal_id == "one"
        app.clock.moment = grant.expires_at
        with pytest.raises(AuthenticationError):
            app.session(grant.token)
        app.clock.moment = FixedClock.moment
        new = app.login("one@example.invalid", "fiction password")
        app.logout(new.token)
        with pytest.raises(AuthenticationError):
            app.session(new.token)
        with pytest.raises(AuthenticationError):
            app.session("unknown")


def test_underage_never_calls_model_or_consumes_invite(repository_url):
    with open_repository(repository_url) as repo:
        issue(repo)
        model = CapturingModel()
        app = app_for(repo, model)
        with pytest.raises(UnderageError):
            app.apply(command(dob=date(2010, 1, 1)))
        assert model.received == []
        assert app.apply(command()).admission is AdmissionStatus.NEEDS_REVIEW


@pytest.mark.parametrize("result", [TimeoutError("Private failure canary"), "Reject", None])
def test_model_failures_never_auto_admit(repository_url, result):
    with open_repository(repository_url) as repo:
        issue(repo)
        app = app_for(repo, CapturingModel(result))
        assert app.apply(command()).admission is AdmissionStatus.NEEDS_REVIEW


def test_admin_rejection_is_human_terminal_and_audited(repository_url):
    from vaeil.domain.authentication import AdmissionConflictError
    with open_repository(repository_url) as repo:
        issue(repo)
        app = app_for(repo)
        app.seed_admin(email="admin@example.invalid", password="admin fiction password")
        app.apply(command())
        actor = app.session(app.login("admin@example.invalid", "admin fiction password").token)
        app.decide_admission(actor=actor, applicant_id="one", decision=AdmissionDecision.REJECT)
        assert app.session(app.login("one@example.invalid", "fiction password").token).admission is AdmissionStatus.REJECTED
        with pytest.raises(AdmissionConflictError):
            app.decide_admission(actor=actor, applicant_id="one", decision=AdmissionDecision.APPROVE)
        with repo.transaction() as unit:
            assert [e.kind.value for e in unit.list_audit(subject_id="one")].count("admission_rejected") == 1
