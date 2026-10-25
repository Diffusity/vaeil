"""T1 identity seam: deliberately incomplete skeleton."""
from dataclasses import dataclass
from datetime import date

@dataclass
class MemberIdentity:
    member_id: str
    legal_name: str
    email: str
    phone: str | None
    date_of_birth: date

class IdentityOwnerMismatchError(Exception):
    pass
