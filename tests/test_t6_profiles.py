"""Private Onboarding drafts become complete Member records only at completion."""
import pytest
from test_t6_application import app_for, command, issue
from vaeil.adapters.persistence import open_repository
from vaeil.domain import Verdict, PseudonymAlreadySetError, PseudonymTakenError
from vaeil.domain.authentication import AccessDeniedError
from vaeil.domain.repository import MemberNotFoundError
from test_t6_application import CapturingModel

pytest_plugins = ["test_repository_contract"]


def fields():
    return dict(relationship_intent="long_term", life_stage="undergraduate", interests=["reading"],
                values=["honesty"], communication_style="direct", pace_and_lifestyle="quiet_and_routine", about="")


def admitted(repo):
    issue(repo)
    app = app_for(repo, CapturingModel(Verdict.APPROVED))
    app.apply(command())
    return app, app.session(app.login("one@example.invalid", "fiction password").token)


def test_private_draft_then_complete_then_profile_update_preserves_identity(repository_url):
    from vaeil.domain.profile import ProfileDraftInput
    from vaeil.domain.member import OwnProfileView
    with open_repository(repository_url) as repo:
        app, actor = admitted(repo)
        draft = app.save_own_profile(actor=actor, draft=ProfileDraftInput(about="  I enjoy quiet walks.  "))
        assert draft.complete is False
        assert draft.values_profile.about == "I enjoy quiet walks."
        with repo.transaction() as unit:
            with pytest.raises(MemberNotFoundError):
                unit.get_member("one")
        complete = app.save_own_profile(actor=actor, draft=ProfileDraftInput(pseudonym="Comet", **fields()))
        assert isinstance(complete, OwnProfileView)
        changed = fields() | {"about": "I enjoy music and quiet walks."}
        updated = app.save_own_profile(actor=actor, draft=ProfileDraftInput(**changed))
        assert updated.pseudonym == complete.pseudonym and updated.legal_name == complete.legal_name
        assert app.own_profile(actor=actor) == updated
        with pytest.raises(PseudonymAlreadySetError):
            app.save_own_profile(actor=actor, draft=ProfileDraftInput(pseudonym="Comet", **fields()))


@pytest.mark.parametrize("changes", [{"about": "Email private@example.invalid"}, {"about": "My name is PrivateCanary"},
                                      {"interests": ["unknown"]}, {"values": ["honesty", "honesty"]}])
def test_draft_writes_use_the_same_profile_safety_policies(repository_url, changes):
    from vaeil.domain.profile import ProfileDraftInput, InvalidValuesProfileError
    with open_repository(repository_url) as repo:
        app, actor = admitted(repo)
        with pytest.raises(InvalidValuesProfileError):
            app.save_own_profile(actor=actor, draft=ProfileDraftInput(**changes))
        assert app.own_profile(actor=actor).complete is False


def test_pending_applicant_cannot_save_or_read_member_profile(repository_url):
    from vaeil.domain.profile import ProfileDraftInput
    with open_repository(repository_url) as repo:
        issue(repo)
        app = app_for(repo)
        app.apply(command())
        actor = app.session(app.login("one@example.invalid", "fiction password").token)
        with pytest.raises(AccessDeniedError):
            app.save_own_profile(actor=actor, draft=ProfileDraftInput(pseudonym="Comet", **fields()))
        with pytest.raises(AccessDeniedError):
            app.own_profile(actor=actor)


def test_taken_pseudonym_does_not_consume_onboarding_retry(repository_url):
    from vaeil.domain.profile import ProfileDraftInput
    from test_repository_contract import example_member
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            unit.add_member(example_member("different", "Comet"))
            unit.commit()
        app, actor = admitted(repo)
        with pytest.raises(PseudonymTakenError):
            app.save_own_profile(actor=actor, draft=ProfileDraftInput(pseudonym="cOmEt", **fields()))
        assert app.save_own_profile(actor=actor, draft=ProfileDraftInput(pseudonym="Orbit", **fields())).pseudonym.value == "Orbit"
