"""Rule 5: heuristic detection of personal identifiers in Member text.

The scan returns a result with reasons; it deliberately has no delivery
status. Escalated handling belongs to the moderation slice.
"""

import pytest

from vaeil.domain import IdentifierReason, scan_identifiers


def reasons_for(text: str) -> set[IdentifierReason]:
    return set(scan_identifiers(text).reasons)


def test_clean_text_reports_no_identifiers() -> None:
    scan = scan_identifiers("I'm 24, see you at 8 for 3 days.")

    assert scan.is_clean is True
    assert scan.is_flagged is False
    assert scan.reasons == ()


def test_detects_email_address() -> None:
    assert reasons_for("Reach me at john.doe@example.com.") == {
        IdentifierReason.EMAIL
    }


def test_detects_phone_number_with_spaces() -> None:
    assert reasons_for("Call me on 98765 43210.") == {IdentifierReason.PHONE}


def test_detects_phone_number_with_dashes() -> None:
    assert reasons_for("Call me on 98765-43210.") == {IdentifierReason.PHONE}


def test_detects_phone_number_with_india_country_code() -> None:
    assert reasons_for("Call +91 98765 43210.") == {IdentifierReason.PHONE}


def test_detects_at_handle() -> None:
    assert reasons_for("I'm @john_doe on Instagram.") == {IdentifierReason.HANDLE}


def test_detects_obfuscated_email() -> None:
    assert reasons_for("john at gmail dot com") == {
        IdentifierReason.OBFUSCATED_EMAIL
    }


def test_detects_bracketed_obfuscated_email() -> None:
    assert reasons_for("john [at] gmail [dot] com") == {
        IdentifierReason.OBFUSCATED_EMAIL
    }


def test_reports_every_reason_present() -> None:
    text = "john@example.com or 98765 43210"

    assert reasons_for(text) == {IdentifierReason.EMAIL, IdentifierReason.PHONE}


@pytest.mark.parametrize(
    "text",
    [
        "I'm 24",
        "see you at 8",
        "3 days",
        "2026-10-22",
    ],
)
def test_ordinary_numbers_are_not_flagged(text: str) -> None:
    assert scan_identifiers(text).is_clean is True
