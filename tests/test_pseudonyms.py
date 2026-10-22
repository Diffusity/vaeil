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
