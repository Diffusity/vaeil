"""Pair-scoped allow-list views; generic private export remains forbidden."""
from dataclasses import dataclass, field
from datetime import date
from vaeil.domain.identity import MemberIdentity
from vaeil.domain.profile import ValuesProfile, build_values_profile
from vaeil.domain.pseudonym import Pseudonym
from vaeil.domain.privacy import PrivateRecord, PrivateText, private_date, reveal_text

@dataclass(frozen=True, slots=True)
class Member(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    identity: MemberIdentity
    pseudonym: Pseudonym
    values_profile: ValuesProfile

    def __post_init__(self) -> None:
        if not isinstance(self.identity, MemberIdentity) or not isinstance(self.pseudonym, Pseudonym) or not isinstance(self.values_profile, ValuesProfile):
            raise TypeError("Use Member identity, Pseudonym and a complete Values Profile.")
        profile = self.values_profile
        validated = build_values_profile(
            owner=self.identity, relationship_intent=profile.relationship_intent,
            life_stage=profile.life_stage, interests=profile.interests, values=profile.values,
            communication_style=profile.communication_style,
            pace_and_lifestyle=profile.pace_and_lifestyle, about=profile.about,
        )
        object.__setattr__(self, "values_profile", validated)

@dataclass(frozen=True, slots=True)
class ConversationRevealState:
    conversation_id: str
    participant_ids: tuple[str, str]
    revealed: bool

    def __post_init__(self) -> None:
        pair = self.participant_ids
        if (
            not isinstance(self.conversation_id, str) or not self.conversation_id
            or not isinstance(pair, tuple) or len(pair) != 2
            or any(not isinstance(participant, str) or not participant for participant in pair)
            or pair[0] == pair[1] or type(self.revealed) is not bool
        ):
            raise InvalidConversationParticipantsError("Use a Conversation ID, two distinct Member IDs and Boolean Reveal state.")

@dataclass(frozen=True, slots=True)
class PreRevealMemberView:
    pseudonym: Pseudonym
    values_profile: ValuesProfile

@dataclass(frozen=True, slots=True)
class RevealedMemberView(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    pseudonym: Pseudonym
    values_profile: ValuesProfile
    legal_name: str = field(repr=False)
    email: str = field(repr=False)
    phone: str | None = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "legal_name", PrivateText(self.legal_name))
        object.__setattr__(self, "email", PrivateText(self.email))
        if self.phone is not None:
            object.__setattr__(self, "phone", PrivateText(self.phone))

@dataclass(frozen=True, slots=True)
class OwnProfileView(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    pseudonym: Pseudonym
    values_profile: ValuesProfile
    legal_name: str = field(repr=False)
    email: str = field(repr=False)
    phone: str | None = field(repr=False)
    date_of_birth: date = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "legal_name", PrivateText(self.legal_name))
        object.__setattr__(self, "email", PrivateText(self.email))
        if self.phone is not None:
            object.__setattr__(self, "phone", PrivateText(self.phone))
        object.__setattr__(self, "date_of_birth", private_date(self.date_of_birth))

class SelfViewerError(Exception):
    pass
class ViewerNotParticipantError(Exception):
    pass
class SubjectNotParticipantError(Exception):
    pass
class InvalidConversationParticipantsError(Exception):
    pass

def project_member_for_viewer(member: Member, *, viewer_id: str, conversation: ConversationRevealState) -> PreRevealMemberView | RevealedMemberView:
    if not isinstance(member, Member) or not isinstance(conversation, ConversationRevealState):
        raise TypeError("Use Member and Conversation view context.")
    identity = member.identity
    if identity.member_id not in conversation.participant_ids:
        raise SubjectNotParticipantError("The subject is outside this Conversation.")
    if viewer_id == identity.member_id:
        raise SelfViewerError("Use the separate own-profile projection.")
    if viewer_id not in conversation.participant_ids:
        raise ViewerNotParticipantError("The viewer is outside this Conversation.")
    if conversation.revealed:
        return RevealedMemberView(member.pseudonym, member.values_profile, identity.legal_name, identity.email, identity.phone)
    return PreRevealMemberView(member.pseudonym, member.values_profile)

def project_own_profile(member: Member) -> OwnProfileView:
    identity = member.identity
    return OwnProfileView(member.pseudonym, member.values_profile, identity.legal_name,
                          identity.email, identity.phone, identity.date_of_birth)

def serialize_member_view(view) -> dict:
    if type(view) not in (PreRevealMemberView, RevealedMemberView, OwnProfileView):
        raise TypeError("Use an explicit authorized view, never a private record.")
    profile = view.values_profile
    result = {
        "pseudonym": view.pseudonym.value,
        "values_profile": {
            "relationship_intent": profile.relationship_intent.value,
            "life_stage": profile.life_stage.value,
            "interests": sorted(choice.value for choice in profile.interests),
            "values": sorted(choice.value for choice in profile.values),
            "communication_style": profile.communication_style.value,
            "pace_and_lifestyle": profile.pace_and_lifestyle.value,
            "about": profile.about,
        },
    }
    if isinstance(view, (RevealedMemberView, OwnProfileView)):
        result.update(legal_name=reveal_text(view.legal_name), email=reveal_text(view.email),
                      phone=None if view.phone is None else reveal_text(view.phone))
    if isinstance(view, OwnProfileView):
        result["date_of_birth"] = view.date_of_birth.isoformat()
    return result
