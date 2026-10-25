"""Private Member identity, separate from all public profile/view fields."""
from dataclasses import dataclass, field
from datetime import date
from vaeil.domain.privacy import PrivateRecord, PrivateText, private_date

@dataclass(frozen=True, slots=True)
class MemberIdentity(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    member_id: str
    legal_name: PrivateText = field(repr=False)
    email: PrivateText = field(repr=False)
    phone: PrivateText | None = field(repr=False)
    date_of_birth: date = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "legal_name", PrivateText(self.legal_name))
        object.__setattr__(self, "email", PrivateText(self.email))
        if self.phone is not None:
            object.__setattr__(self, "phone", PrivateText(self.phone))
        object.__setattr__(self, "date_of_birth", private_date(self.date_of_birth))

class IdentityOwnerMismatchError(Exception):
    """The supplied identity does not belong to the claiming Member."""
