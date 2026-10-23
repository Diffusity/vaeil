"""In-memory Pseudonym claims; persistence belongs to a later adapter."""

from dataclasses import dataclass
import unicodedata

from vaeil.domain.identifiers import scan_identifiers

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

    def claim(self, member_id: str, candidate: str) -> Pseudonym:
        if member_id in self._members:
            raise PseudonymAlreadySetError("Pseudonym is fixed once set.")

        value = unicodedata.normalize("NFKC", candidate).strip()
        if scan_identifiers(value).is_flagged:
            raise InvalidPseudonymError("Choose a non-identifying Pseudonym.")

        if (
            not MIN_PSEUDONYM_LENGTH <= len(value) <= MAX_PSEUDONYM_LENGTH
            or not value[0].isalpha()
            or not all(char.isalpha() or char.isdecimal() or char in PSEUDONYM_PUNCTUATION for char in value)
        ):
            raise InvalidPseudonymError("Use 3-20 letters, digits, underscores or hyphens; start with a letter.")

        key = value.casefold()
        if key in RESERVED_PSEUDONYMS:
            raise InvalidPseudonymError("Choose a name that does not impersonate staff.")
        if key in self._taken:
            raise PseudonymTakenError("Pseudonym is already taken.")

        pseudonym = Pseudonym(value)
        self._members[member_id] = pseudonym
        self._taken.add(key)
        return pseudonym
