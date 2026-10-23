"""Rule 5: heuristic detection of personal identifiers in Member text.

The scan returns a result with reasons; it deliberately has no delivery
status. Escalated handling belongs to the moderation slice.
"""

import pytest
from dataclasses import fields

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


@pytest.mark.parametrize("text", [
    "9876543210", "(98765) 43210", "98765.43210", "0091 98765 43210",
    "+91 9876543210", "9 8 7 6 5 4 3 2 1 0", "９８７６５４３２１０",
    "٩٨٧٦٥٤٣٢١٠", "12345678901234567890",
])
def test_supported_phone_formats(text: str) -> None:
    assert IdentifierReason.PHONE in reasons_for(text)


@pytest.mark.parametrize("text, flagged", [("123456789", False), ("1234567890", True)])
def test_phone_digit_threshold_boundary(text: str, flagged: bool) -> None:
    from vaeil.domain.identifiers import MIN_PHONE_DIGITS

    assert MIN_PHONE_DIGITS == 10
    assert scan_identifiers(text).is_flagged is flagged


@pytest.mark.parametrize("text, names", [
    ("@name", ("HANDLE",)),
    ("instagram.com/name", ("HANDLE", "URL")),
    ("insta: name", ("HANDLE",)),
    ("my ig is name", ("HANDLE",)),
    ("https://example.com/path", ("URL",)),
    ("www.example.com", ("URL",)),
    ("example.org/profile", ("URL",)),
])
def test_handles_and_links_have_explicit_reasons(text: str, names: tuple[str, ...]) -> None:
    assert tuple(reason.name for reason in scan_identifiers(text).reasons) == names


@pytest.mark.parametrize("text", [
    "john (at) gmail (dot) com", "john [at] gmail [dot] com",
    "john at gmail dot com", "john at gmail d0t com",
    "JoHn (AT) GMAIL (D0T) COM",
])
def test_supported_email_obfuscations(text: str) -> None:
    assert IdentifierReason.OBFUSCATED_EMAIL in reasons_for(text)


@pytest.mark.parametrize("text", [
    "10:30", "2026-10-22", "Rs 5000", "3 days", "I'm 24", "see you at 8",
    "call me at 8pm", "room 204", "5 km",
])
def test_non_identifier_numbers_stay_clean(text: str) -> None:
    assert scan_identifiers(text).is_clean


def test_all_reasons_are_reported_in_a_stable_order() -> None:
    text = "john@example.com 9876543210 @john john at gmail dot com https://example.org"
    expected = ("EMAIL", "PHONE", "HANDLE", "OBFUSCATED_EMAIL", "URL")
    assert tuple(reason.name for reason in scan_identifiers(text).reasons) == expected
    assert scan_identifiers(text) == scan_identifiers(text)


@pytest.mark.parametrize("text", ["", "   \t\n", "ordinary text " * 100000], ids=["empty", "whitespace", "long"])
def test_empty_and_long_clean_inputs(text: str) -> None:
    assert scan_identifiers(text).is_clean


def test_scan_stores_only_reasons_and_no_identifier_text() -> None:
    scan = scan_identifiers("john@example.com")
    assert [field.name for field in fields(scan)] == ["reasons"]
    assert "john@example.com" not in repr(scan)
    assert not hasattr(scan, "delivery_status")
