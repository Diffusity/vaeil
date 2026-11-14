"""Private principal records; roles and human admission decisions are server-owned."""
from dataclasses import dataclass, field
from enum import Enum
import unicodedata
from vaeil.domain.identity import MemberIdentity
from vaeil.domain.privacy import PrivateRecord, PrivateText
from vaeil.domain.admission import validate_application_note


class Role(str, Enum):
    APPLICANT = "applicant"
    MEMBER = "member"
    ADMIN = "admin"


class AdmissionStatus(str, Enum):
    NEEDS_REVIEW = "NeedsReview"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class AdmissionDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class AdmissionConflictError(Exception):
    """A missing or already decided application cannot be decided again."""


class AuthenticationError(Exception):
    """Authentication failed; neither account existence nor private input is echoed."""


class AccessDeniedError(Exception):
    """Current server-owned authority does not permit the operation."""


def normalize_login_email(email: str) -> str:
    if not isinstance(email, str):
        raise AuthenticationError("Invalid credentials.")
    key = unicodedata.normalize("NFKC", email.strip()).casefold()
    if (key.count("@") != 1 or not all(key.split("@"))
            or any(character.isspace() or unicodedata.category(character).startswith("C") for character in key)):
        raise AuthenticationError("Invalid credentials.")
    return key


@dataclass(frozen=True, slots=True)
class PrincipalRecord(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    identity: MemberIdentity = field(repr=False)
    login_email: PrivateText = field(repr=False)
    password_hash: PrivateText = field(repr=False)
    role: Role
    admission: AdmissionStatus

    def __post_init__(self):
        if (not isinstance(self.identity, MemberIdentity) or not isinstance(self.role, Role)
                or not isinstance(self.admission, AdmissionStatus)
                or (self.role in {Role.MEMBER, Role.ADMIN} and self.admission is not AdmissionStatus.APPROVED)
                or (self.role is Role.APPLICANT and self.admission is AdmissionStatus.APPROVED)):
            raise TypeError("Use a typed principal and consistent server-owned admission state.")
        object.__setattr__(self, "login_email", PrivateText(self.login_email))
        object.__setattr__(self, "password_hash", PrivateText(self.password_hash))


@dataclass(frozen=True, slots=True)
class ApplicationRecord(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    principal: PrincipalRecord = field(repr=False)
    note: str = field(repr=False)

    def __post_init__(self):
        if not isinstance(self.principal, PrincipalRecord) or self.principal.role is Role.ADMIN:
            raise TypeError("Use an Applicant principal.")
        object.__setattr__(self, "note", validate_application_note(self.note, owner=self.principal.identity))
