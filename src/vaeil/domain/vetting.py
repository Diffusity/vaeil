"""Rule 2 (vetting never rejects) and the fail-closed LLM boundary."""

from enum import Enum
from typing import Protocol

from vaeil.domain.applicant import Applicant


class Verdict(Enum):
    """The only outcomes vetting can produce; rejection is unrepresentable."""

    APPROVED = "Approved"
    NEEDS_REVIEW = "NeedsReview"


class VettingModel(Protocol):
    """Port for the LLM vetting boundary; adapters translate model output."""

    def vet(self, applicant: Applicant) -> Verdict:
        ...


def vet(applicant: Applicant, model: VettingModel) -> Verdict:
    """Run vetting, failing closed to NeedsReview on any port misbehaviour."""
    try:
        verdict = model.vet(applicant)
    except Exception:
        return Verdict.NEEDS_REVIEW

    if not isinstance(verdict, Verdict):
        return Verdict.NEEDS_REVIEW

    return verdict
