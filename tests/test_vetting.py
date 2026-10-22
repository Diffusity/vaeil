from datetime import date

from vaeil.domain import Applicant, Verdict, vet


class FakeVettingModel:
    """A test double for the LLM port; it can only return a Verdict."""

    def __init__(self, verdict: Verdict) -> None:
        self._verdict = verdict

    def vet(self, applicant: Applicant) -> Verdict:
        return self._verdict


def an_applicant() -> Applicant:
    return Applicant(date_of_birth=date(2000, 1, 1))


def test_verdict_cannot_represent_rejection() -> None:
    assert {member.value for member in Verdict} == {"Approved", "NeedsReview"}
    assert not hasattr(Verdict, "REJECT")


def test_approved_verdict_is_returned() -> None:
    assert vet(an_applicant(), FakeVettingModel(Verdict.APPROVED)) is Verdict.APPROVED


def test_needs_review_verdict_is_returned() -> None:
    assert vet(an_applicant(), FakeVettingModel(Verdict.NEEDS_REVIEW)) is Verdict.NEEDS_REVIEW
