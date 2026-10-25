"""T1 shared self-name seam: deliberately incomplete skeleton."""
from enum import Enum
from vaeil.domain.identity import MemberIdentity

class SelfNameMode(Enum):
    PSEUDONYM = "pseudonym"
    ABOUT = "about"

def contains_self_name(text: str, *, identity: MemberIdentity, mode: SelfNameMode) -> bool:
    raise NotImplementedError("T1 self-name predicate")
