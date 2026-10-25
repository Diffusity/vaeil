"""Rule 1 (invite-only access) and Rule 6 (age gate) at the domain seam.

Leap-day rule: a 29 February birthday turns 18 on 28 February in non-leap
years. That is the date used by the age comparison, so the rule is testable
without depending on the real clock.
"""

from dataclasses import dataclass
from datetime import date

from vaeil.domain.applicant import Applicant
from vaeil.domain.clock import Clock
from vaeil.domain.privacy import PrivateRecord, PrivateDate, private_date


class UnderageError(Exception):
    """The Applicant is under 18 on the Clock's date."""


class FutureDateOfBirthError(Exception):
    """The date of birth is after the Clock's date."""


class InvalidInviteError(Exception):
    """The Invite is unknown or malformed."""


class InviteAlreadyRedeemedError(Exception):
    """The Invite has already been used by an Applicant."""


@dataclass(slots=True)
class Invite(PrivateRecord):
    code: str
    issuer: str
    redeemed_by: Applicant | None = None

    @property
    def is_redeemed(self) -> bool:
        return self.redeemed_by is not None


def redeem_invite(
    invite: Invite | None,
    date_of_birth: date | PrivateDate,
    clock: Clock,
) -> Applicant:
    """Redeem a single-use Invite for an 18+ Applicant.

    Age is checked before the Invite is touched, so an underage Applicant
    gets UnderageError even when the Invite is unknown or already used.
    """
    today = clock.today()
    birth = private_date(date_of_birth).UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()

    if birth > today:
        raise FutureDateOfBirthError("Date of birth cannot be in the future.")

    if not (today >= _eighteenth_birthday(birth)):
        raise UnderageError("Applicant must be 18 or older to redeem an Invite.")

    if invite is None or not invite.code.strip():
        raise InvalidInviteError("Invite is unknown or invalid.")

    if invite.is_redeemed:
        raise InviteAlreadyRedeemedError("Invite has already been redeemed.")

    applicant = Applicant(date_of_birth=date_of_birth)
    invite.redeemed_by = applicant
    return applicant


def _eighteenth_birthday(date_of_birth: date) -> date:
    try:
        return date_of_birth.replace(year=date_of_birth.year + 18)
    except ValueError:
        # 29 February is clamped to 28 February in non-leap years.
        return date_of_birth.replace(year=date_of_birth.year + 18, day=28)
