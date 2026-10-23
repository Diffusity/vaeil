"""Heuristic identifier scanning; delivery decisions belong to moderation."""

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

MIN_PHONE_DIGITS = 10


class IdentifierReason(Enum):
    EMAIL = "email"
    PHONE = "phone"
    HANDLE = "handle"
    OBFUSCATED_EMAIL = "obfuscated_email"
    URL = "url"


@dataclass(frozen=True)
class IdentifierScan:
    reasons: tuple[IdentifierReason, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.reasons

    @property
    def is_flagged(self) -> bool:
        return bool(self.reasons)


def scan_identifiers(text: str) -> IdentifierScan:
    """Report supported identifier patterns, without deciding delivery.

    A clean result is not proof of anonymity. Real names, spelled-out
    numbers, and identifiers split across messages can be missed.
    """
    normalized = unicodedata.normalize("NFKC", text)
    normalized = "".join(
        str(unicodedata.decimal(char)) if char.isdecimal() else char
        for char in normalized
    )
    found = {
        reason for reason, pattern in _PATTERNS if pattern.search(normalized)
    }
    if any(
        sum(char.isdecimal() for char in match.group()) >= MIN_PHONE_DIGITS
        for match in _PHONE_RUN.finditer(normalized)
    ):
        found.add(IdentifierReason.PHONE)
    return IdentifierScan(tuple(reason for reason in IdentifierReason if reason in found))


_PHONE_RUN = re.compile(r"\d(?:[\s().+-]*\d)*")
_PATTERNS = (
    (IdentifierReason.EMAIL, re.compile(
        r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE
    )),
    (IdentifierReason.HANDLE, re.compile(
        r"(?<![\w.+-])@\w+|\b(?:instagram\.com/\w+|insta\s*:\s*\w+|my\s+ig\s+is\s+\w+)",
        re.IGNORECASE,
    )),
    (IdentifierReason.OBFUSCATED_EMAIL, re.compile(
        # Retry only at token starts, not after every internal dot/hyphen.
        r"(?<![\w.+-])\b[\w.+-]+\s+(?:at|\[at\]|\(at\))\s+[\w-]+"
        r"\s+(?:d[o0]t|\[d[o0]t\]|\(d[o0]t\))\s+[a-z]{2,}\b", re.IGNORECASE
    )),
    (IdentifierReason.URL, re.compile(
        r"\b(?:https?://|www\.)[^\s]+|(?<![\w@.-])(?![\w.-]*@)[\w-]+(?:\.[\w-]+)*"
        r"\.[a-z]{2,}(?:/[^\s]*)?", re.IGNORECASE
    )),
)
