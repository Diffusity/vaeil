"""Pure domain core: no frameworks, no database, no LLM SDK."""

from vaeil.domain.applicant import Applicant
from vaeil.domain.clock import Clock
from vaeil.domain.identifiers import IdentifierReason, IdentifierScan, scan_identifiers
from vaeil.domain.invite import (
    FutureDateOfBirthError,
    Invite,
    InviteAlreadyRedeemedError,
    InvalidInviteError,
    UnderageError,
    redeem_invite,
)
from vaeil.domain.vetting import Verdict, VettingModel, vet
from vaeil.domain.pseudonym import (
    InvalidPseudonymError,
    Pseudonym,
    PseudonymAlreadySetError,
    PseudonymDirectory,
    PseudonymTakenError,
)

__all__ = [
    "Applicant",
    "Clock",
    "IdentifierReason",
    "IdentifierScan",
    "FutureDateOfBirthError",
    "Invite",
    "InviteAlreadyRedeemedError",
    "InvalidInviteError",
    "InvalidPseudonymError",
    "Pseudonym",
    "PseudonymAlreadySetError",
    "PseudonymDirectory",
    "PseudonymTakenError",
    "UnderageError",
    "Verdict",
    "VettingModel",
    "redeem_invite",
    "scan_identifiers",
    "vet",
]
