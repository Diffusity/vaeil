from datetime import date

import pytest

from vaeil.domain import Invite, UnderageError, redeem_invite

TODAY = date(2026, 10, 22)


class FakeClock:
    """A Clock fixed to one date; tests never depend on the real clock."""

    def __init__(self, today: date) -> None:
        self._today = today

    def today(self) -> date:
        return self._today


def an_unused_invite() -> Invite:
    return Invite(code="INVITE-001", issuer="admin")


def test_underage_applicant_is_refused() -> None:
    invite = an_unused_invite()

    with pytest.raises(UnderageError):
        redeem_invite(
            invite=invite,
            date_of_birth=date(2010, 1, 1),  # 16 on TODAY
            clock=FakeClock(TODAY),
        )


def test_underage_attempt_leaves_the_invite_unused() -> None:
    invite = an_unused_invite()

    with pytest.raises(UnderageError):
        redeem_invite(
            invite=invite,
            date_of_birth=date(2008, 10, 23),  # turns 18 tomorrow
            clock=FakeClock(TODAY),
        )

    assert invite.is_redeemed is False


def test_eighteenth_birthday_today_can_redeem() -> None:
    invite = an_unused_invite()

    applicant = redeem_invite(
        invite=invite,
        date_of_birth=date(2008, 10, 22),  # exactly 18 on TODAY
        clock=FakeClock(TODAY),
    )

    assert applicant.date_of_birth == date(2008, 10, 22)
    assert invite.is_redeemed is True
