"""In-memory Pseudonym claims; persistence belongs to a later adapter."""

from dataclasses import dataclass


MIN_PSEUDONYM_LENGTH = 3
MAX_PSEUDONYM_LENGTH = 20
PSEUDONYM_PUNCTUATION = frozenset("_-")
RESERVED_PSEUDONYMS = frozenset({"admin", "moderator", "system", "vaeil", "support"})


class InvalidPseudonymError(Exception):
    """The proposed Pseudonym is blank or contains a detected identifier."""


class PseudonymTakenError(Exception):
    """Another Member already holds this Pseudonym."""


class PseudonymAlreadySetError(Exception):
    """The Member already has a fixed Pseudonym."""


@dataclass(frozen=True)
class Pseudonym:
    value: str


class PseudonymDirectory:
    """Own claims within one directory; reuse it across Members.

    This is not persistent storage or a cross-process uniqueness guarantee.
    Identifier validation inherits the scanner's heuristic limitations.
    """

    def __init__(self) -> None:
        self._members: dict[str, Pseudonym] = {}
        self._taken: set[str] = set()

    def claim(self, member_id: str, candidate: str, *, identity) -> Pseudonym:
        raise NotImplementedError("T1 identity-aware claim")
