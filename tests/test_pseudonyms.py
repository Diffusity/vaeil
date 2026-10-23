"""Rule 5: Pseudonym validation shares the identifier check and is fixed once set."""

import pytest

from vaeil.domain import (
    InvalidPseudonymError,
    PseudonymAlreadySetError,
    PseudonymDirectory,
    PseudonymTakenError,
)


def test_a_valid_pseudonym_is_claimed() -> None:
    directory = PseudonymDirectory()

    pseudonym = directory.claim("member-1", "Comet")

    assert pseudonym.value == "Comet"


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_pseudonym_is_rejected(blank: str) -> None:
    with pytest.raises(InvalidPseudonymError):
        PseudonymDirectory().claim("member-1", blank)


@pytest.mark.parametrize(
    "candidate",
    [
        "john@example.com",
        "98765 43210",
        "@john_doe",
        "john at gmail dot com",
    ],
)
def test_identifier_like_pseudonym_is_rejected(candidate: str) -> None:
    with pytest.raises(InvalidPseudonymError):
        PseudonymDirectory().claim("member-1", candidate)


def test_pseudonyms_are_unique_case_insensitively() -> None:
    directory = PseudonymDirectory()
    directory.claim("member-1", "Comet")

    with pytest.raises(PseudonymTakenError):
        directory.claim("member-2", "cOmEt")


def test_pseudonym_is_fixed_once_set() -> None:
    directory = PseudonymDirectory()
    directory.claim("member-1", "Comet")

    with pytest.raises(PseudonymAlreadySetError):
        directory.claim("member-1", "Nova")


def test_a_failed_claim_does_not_set_the_pseudonym() -> None:
    directory = PseudonymDirectory()

    with pytest.raises(InvalidPseudonymError):
        directory.claim("member-1", "")

    assert directory.claim("member-1", "Comet").value == "Comet"


def test_a_failed_taken_claim_does_not_set_the_member() -> None:
    directory = PseudonymDirectory()
    directory.claim("member-1", "Comet")

    with pytest.raises(PseudonymTakenError):
        directory.claim("member-2", "comet")

    assert directory.claim("member-2", "Nova").value == "Nova"


@pytest.mark.parametrize("candidate", [" cOmEt ", "Ｃomet"])
def test_normalized_names_share_one_claim(candidate: str) -> None:
    directory = PseudonymDirectory()
    directory.claim("one", "Comet")
    with pytest.raises(PseudonymTakenError):
        directory.claim("two", candidate)


def test_display_value_is_trimmed_and_nfkc_normalized() -> None:
    assert PseudonymDirectory().claim("one", " Ｃomet ").value == "Comet"


@pytest.mark.parametrize("candidate, valid", [
    ("Ab", False), ("Abc", True), ("A" * 20, True), ("A" * 21, False),
    ("A_1-b", True), ("1Comet", False), ("_Comet", False), ("-Comet", False),
    ("Co met", False), ("Comet!", False), ("Comet.Star", False),
    ("Étoile", True),
])
def test_pseudonym_format_boundaries(candidate: str, valid: bool) -> None:
    from vaeil.domain.pseudonym import MIN_PSEUDONYM_LENGTH, MAX_PSEUDONYM_LENGTH

    assert (MIN_PSEUDONYM_LENGTH, MAX_PSEUDONYM_LENGTH) == (3, 20)
    if valid:
        assert PseudonymDirectory().claim("one", candidate).value == candidate
    else:
        with pytest.raises(InvalidPseudonymError):
            PseudonymDirectory().claim("one", candidate)


@pytest.mark.parametrize("candidate", ["admin", "MODERATOR", "System", "vaeil", "Support"])
def test_reserved_names_are_refused(candidate: str) -> None:
    with pytest.raises(InvalidPseudonymError):
        PseudonymDirectory().claim("one", candidate)


def test_claiming_the_same_name_twice_is_still_a_change_attempt() -> None:
    directory = PseudonymDirectory()
    directory.claim("one", "Comet")
    with pytest.raises(PseudonymAlreadySetError):
        directory.claim("one", "Comet")


def test_format_valid_phone_identifier_is_refused() -> None:
    with pytest.raises(InvalidPseudonymError):
        PseudonymDirectory().claim("one", "Comet9876543210")
