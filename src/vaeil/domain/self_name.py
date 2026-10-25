"""Heuristic own-name checks, deliberately different for names and About."""
from enum import Enum
import re
import unicodedata
from vaeil.domain.identity import MemberIdentity

class SelfNameMode(Enum):
    PSEUDONYM = "pseudonym"
    ABOUT = "about"

def contains_self_name(text: str, *, identity: MemberIdentity, mode: SelfNameMode) -> bool:
    if not isinstance(text, str) or not isinstance(identity, MemberIdentity) or not isinstance(mode, SelfNameMode):
        raise TypeError("Use text, Member identity and an explicit self-name mode.")
    name = unicodedata.normalize("NFKC", identity.legal_name).casefold()
    local = unicodedata.normalize("NFKC", identity.email).casefold().partition("@")[0]
    tokens = frozenset(token for token in re.split(r"[\s._+\-]+", name + " " + local) if len(token) >= 3)
    normalized = unicodedata.normalize("NFKC", text).casefold()
    if mode is SelfNameMode.PSEUDONYM:
        return any(token in normalized for token in tokens)
    if not tokens:
        return False
    # Boundaries prevent repeated suffix scans and allow punctuation/apostrophes.
    alternatives = "|".join(re.escape(token) for token in sorted(tokens, key=lambda token: (-len(token), token)))
    return re.search(r"(?<!\w)(?:" + alternatives + r")(?!\w)", normalized) is not None
