"""Rule 5: Pseudonym validation shares the identifier check and is fixed once set."""

from datetime import date

import pytest

from vaeil import domain as d

from vaeil.domain import (
    InvalidPseudonymError,
    PseudonymAlreadySetError,
    PseudonymDirectory,
    PseudonymTakenError,
)


def claim(directory, member_id, candidate, *, owner=None):
    owner = owner if owner is not None else d.MemberIdentity(member_id=member_id, legal_name="PrivateNameZXQ",
                           email="privateownerzxq@example.invalid", phone=None,
                           date_of_birth=date(1998, 7, 23))
    return directory.claim(member_id, candidate, identity=owner)


def test_a_valid_pseudonym_is_claimed() -> None:
    directory = PseudonymDirectory()

    pseudonym = claim(directory, "member-1", "Comet")

    assert pseudonym.value == "Comet"


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_pseudonym_is_rejected(blank: str) -> None:
    with pytest.raises(InvalidPseudonymError):
        claim(PseudonymDirectory(), "member-1", blank)


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
        claim(PseudonymDirectory(), "member-1", candidate)


def test_pseudonyms_are_unique_case_insensitively() -> None:
    directory = PseudonymDirectory()
    claim(directory, "member-1", "Comet")

    with pytest.raises(PseudonymTakenError):
        claim(directory, "member-2", "cOmEt")


def test_pseudonym_is_fixed_once_set() -> None:
    directory = PseudonymDirectory()
    claim(directory, "member-1", "Comet")

    with pytest.raises(PseudonymAlreadySetError):
        claim(directory, "member-1", "Nova")


def test_a_failed_claim_does_not_set_the_pseudonym() -> None:
    directory = PseudonymDirectory()

    with pytest.raises(InvalidPseudonymError):
        claim(directory, "member-1", "")

    assert claim(directory, "member-1", "Comet").value == "Comet"


@pytest.mark.parametrize("scenario", ["slice2-taken", "merged-t1-fullwidth-taken"])
def test_a_failed_taken_claim_does_not_set_the_member(scenario) -> None:
    directory = PseudonymDirectory()
    first, second = ("member-1", "member-2") if scenario == "slice2-taken" else ("one", "two")
    candidate = "comet" if scenario == "slice2-taken" else " ＣＯＭＥＴ "
    owners = {key: None for key in (first, second)}
    if scenario != "slice2-taken":
        owners = {key: d.MemberIdentity(
            member_id=key, legal_name="CanaryNameZXQ", email="canarylocalzxq@example.invalid",
            phone="+919876543210", date_of_birth=date(1987, 3, 14),
        ) for key in (first, second)}
    claim(directory, first, "Comet", owner=owners[first])
    with pytest.raises(PseudonymTakenError):
        claim(directory, second, candidate, owner=owners[second])
    assert claim(directory, second, "Nova", owner=owners[second]).value == "Nova"


@pytest.mark.parametrize("candidate", [" cOmEt ", "Ｃomet"])
def test_normalized_names_share_one_claim(candidate: str) -> None:
    directory = PseudonymDirectory()
    claim(directory, "one", "Comet")
    with pytest.raises(PseudonymTakenError):
        claim(directory, "two", candidate)


def test_display_value_is_trimmed_and_nfkc_normalized() -> None:
    assert claim(PseudonymDirectory(), "one", " Ｃomet ").value == "Comet"


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
        assert claim(PseudonymDirectory(), "one", candidate).value == candidate
    else:
        with pytest.raises(InvalidPseudonymError):
            claim(PseudonymDirectory(), "one", candidate)


@pytest.mark.parametrize("candidate", ["admin", "MODERATOR", "System", "vaeil", "Support"])
def test_reserved_names_are_refused(candidate: str) -> None:
    with pytest.raises(InvalidPseudonymError):
        claim(PseudonymDirectory(), "one", candidate)


@pytest.mark.parametrize("member_id", ["one", "subject"], ids=["slice2", "merged-t1"])
def test_claiming_the_same_name_twice_is_still_a_change_attempt(member_id) -> None:
    directory = PseudonymDirectory()
    owner = None if member_id == "one" else d.MemberIdentity(
        member_id=member_id, legal_name="CanaryNameZXQ", email="canarylocalzxq@example.invalid",
        phone="+919876543210", date_of_birth=date(1987, 3, 14),
    )
    claim(directory, member_id, "Comet", owner=owner)
    with pytest.raises(PseudonymAlreadySetError):
        claim(directory, member_id, "Comet", owner=owner)


def test_format_valid_phone_identifier_is_refused() -> None:
    with pytest.raises(InvalidPseudonymError):
        claim(PseudonymDirectory(), "one", "Comet9876543210")
