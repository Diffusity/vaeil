"""T1 views: deliberately mutable skeleton; projection/encoding unimplemented."""
from dataclasses import dataclass
from datetime import date
from vaeil.domain.identity import MemberIdentity
from vaeil.domain.profile import ValuesProfile
from vaeil.domain.pseudonym import Pseudonym

@dataclass
class Member:
    identity: MemberIdentity
    pseudonym: Pseudonym
    values_profile: ValuesProfile

@dataclass
class ConversationRevealState:
    conversation_id: str
    participant_ids: tuple[str, str]
    revealed: bool

@dataclass
class PreRevealMemberView:
    pseudonym: Pseudonym
    values_profile: ValuesProfile

@dataclass
class RevealedMemberView:
    pseudonym: Pseudonym
    values_profile: ValuesProfile
    legal_name: str
    email: str
    phone: str | None

@dataclass
class OwnProfileView:
    pseudonym: Pseudonym
    values_profile: ValuesProfile
    legal_name: str
    email: str
    phone: str | None
    date_of_birth: date

class SelfViewerError(Exception):
    pass
class ViewerNotParticipantError(Exception):
    pass
class SubjectNotParticipantError(Exception):
    pass
class InvalidConversationParticipantsError(Exception):
    pass

def project_member_for_viewer(member: Member, *, viewer_id: str, conversation: ConversationRevealState) -> PreRevealMemberView | RevealedMemberView:
    raise NotImplementedError("T1 viewer projection")

def project_own_profile(member: Member) -> OwnProfileView:
    raise NotImplementedError("T1 owner projection")

def serialize_member_view(view) -> dict:
    raise NotImplementedError("T1 explicit view encoder")
