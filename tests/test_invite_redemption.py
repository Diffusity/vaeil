"""Rule 1 (invite-only) and Rule 6 (age gate) at the `vaeil.domain` seam.

Leap-day rule: someone born on 29 February is treated as having their
birthday on 28 February in non-leap years. So in 2026 (not a leap year)
they turn 18 on 2026-02-28, not 2026-03-01.

At this seam an unknown Invite is represented by `None`; looking up a code
in a repository arrives in a later slice.
"""

from datetime import date

import pytest

from vaeil.domain import (
    Applicant,
    FutureDateOfBirthError,
    Invite,
    InviteAlreadyRedeemedError,
    InvalidInviteError,
    UnderageError,
    redeem_invite,
)

TODAY = date(2026, 10, 22)


class FakeClock:
    """A Clock fixed to one date; tests never depend on the real clock."""

    def __init__(self, today: date) -> None:
        self._today = today

    def today(self) -> date:
        return self._today


def an_unused_invite() -> Invite:
    return Invite(code="INVITE-001", issuer="admin")


def redeem(
    invite: Invite | None,
    date_of_birth: date,
    today: date = TODAY,
) -> Applicant:
    return redeem_invite(
        invite=invite,
        date_of_birth=date_of_birth,
        clock=FakeClock(today),
    )


def test_underage_applicant_is_refused() -> None:
    with pytest.raises(UnderageError):
        redeem(an_unused_invite(), date(2010, 1, 1))  # 16 on TODAY


def test_underage_attempt_leaves_the_invite_unused() -> None:
    invite = an_unused_invite()

    with pytest.raises(UnderageError):
        redeem(invite, date(2008, 10, 23))  # turns 18 tomorrow

    assert invite.is_redeemed is False


def test_turning_eighteen_today_is_allowed() -> None:
    invite = an_unused_invite()

    applicant = redeem(invite, date(2008, 10, 22))  # exactly 18 on TODAY

    assert applicant.date_of_birth == date(2008, 10, 22)
    assert invite.is_redeemed is True


def test_turned_eighteen_yesterday_is_allowed() -> None:
    invite = an_unused_invite()

    applicant = redeem(invite, date(2008, 10, 21))  # turned 18 yesterday

    assert applicant.date_of_birth == date(2008, 10, 21)
    assert invite.redeemed_by is applicant


def test_turning_eighteen_tomorrow_is_refused() -> None:
    with pytest.raises(UnderageError):
        redeem(an_unused_invite(), date(2008, 10, 23))  # turns 18 tomorrow


def test_leap_day_birthday_turns_eighteen_on_feb_28_in_non_leap_years() -> None:
    invite = an_unused_invite()

    applicant = redeem(
        invite,
        date(2008, 2, 29),
        today=date(2026, 2, 28),  # 2026 is not a leap year
    )

    assert applicant.date_of_birth == date(2008, 2, 29)
    assert invite.is_redeemed is True


def test_leap_day_birthday_is_allowed_on_mar_1_in_non_leap_years() -> None:
    invite = an_unused_invite()

    applicant = redeem(invite, date(2008, 2, 29), today=date(2026, 3, 1))

    assert applicant.date_of_birth == date(2008, 2, 29)


def test_future_date_of_birth_is_refused_with_its_own_error() -> None:
    invite = an_unused_invite()

    with pytest.raises(FutureDateOfBirthError):
        redeem(invite, date(2026, 10, 23))  # tomorrow

    assert invite.is_redeemed is False


def test_redeeming_an_already_redeemed_invite_is_refused() -> None:
    invite = an_unused_invite()
    first_applicant = redeem(invite, date(2000, 1, 1))

    with pytest.raises(InviteAlreadyRedeemedError):
        redeem(invite, date(1999, 1, 1))

    assert invite.redeemed_by is first_applicant


def test_unknown_invite_is_refused() -> None:
    with pytest.raises(InvalidInviteError):
        redeem(None, date(2000, 1, 1))


def test_invite_with_a_blank_code_is_refused() -> None:
    invite = Invite(code="   ", issuer="admin")

    with pytest.raises(InvalidInviteError):
        redeem(invite, date(2000, 1, 1))


def test_underage_error_wins_over_an_invalid_invite() -> None:
    """Age is checked before the Invite is touched, so this is not InvalidInviteError."""

    with pytest.raises(UnderageError):
        redeem(None, date(2010, 1, 1))


def test_age_check_uses_the_injected_clock_not_the_real_date() -> None:
    # 1990-01-01 is 10 on the injected 2000-01-01 clock, but an adult on
    # every real date after 2008. A real-clock implementation would accept
    # this Applicant, so the fake and real outcomes never converge.
    with pytest.raises(UnderageError):
        redeem(an_unused_invite(), date(1990, 1, 1), today=date(2000, 1, 1))
