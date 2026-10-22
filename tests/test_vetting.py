"""Rule 2 (vetting never rejects) and the fail-closed LLM boundary."""

from datetime import date

from vaeil.domain import Applicant, Verdict, vet


class FakeVettingModel:
    """A well-behaved test double for the LLM port."""

    def __init__(self, verdict: Verdict) -> None:
        self._verdict = verdict

    def vet(self, applicant: Applicant) -> Verdict:
        return self._verdict


class RaisingVettingModel:
    """A port that fails instead of returning a verdict."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def vet(self, applicant: Applicant) -> Verdict:
        raise self._error


class MisbehavingVettingModel:
    """A port that returns something that is not a Verdict."""

    def __init__(self, result: object) -> None:
        self._result = result

    def vet(self, applicant: Applicant) -> Verdict:
        return self._result  # type: ignore[return-value]


def an_applicant() -> Applicant:
    return Applicant(date_of_birth=date(2000, 1, 1))


def test_verdict_cannot_represent_rejection() -> None:
    assert {member.value for member in Verdict} == {"Approved", "NeedsReview"}
    assert not hasattr(Verdict, "REJECT")


def test_approved_verdict_is_returned() -> None:
    assert vet(an_applicant(), FakeVettingModel(Verdict.APPROVED)) is Verdict.APPROVED


def test_needs_review_verdict_is_returned() -> None:
    assert (
        vet(an_applicant(), FakeVettingModel(Verdict.NEEDS_REVIEW))
        is Verdict.NEEDS_REVIEW
    )


def test_port_error_fails_closed_to_needs_review() -> None:
    model = RaisingVettingModel(RuntimeError("LLM unavailable"))

    assert vet(an_applicant(), model) is Verdict.NEEDS_REVIEW


def test_port_timeout_fails_closed_to_needs_review() -> None:
    model = RaisingVettingModel(TimeoutError("LLM timed out"))

    assert vet(an_applicant(), model) is Verdict.NEEDS_REVIEW


def test_non_verdict_result_fails_closed_to_needs_review() -> None:
    model = MisbehavingVettingModel("Reject")

    assert vet(an_applicant(), model) is Verdict.NEEDS_REVIEW


def test_none_result_fails_closed_to_needs_review() -> None:
    model = MisbehavingVettingModel(None)

    assert vet(an_applicant(), model) is Verdict.NEEDS_REVIEW
