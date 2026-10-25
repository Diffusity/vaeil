"""Pure domain core: no frameworks, no database, no LLM SDK."""

from vaeil.domain.applicant import Applicant
from vaeil.domain.clock import Clock
from vaeil.domain.identifiers import IdentifierReason, IdentifierScan, scan_identifiers
from vaeil.domain.invite import (
    FutureDateOfBirthError,
    Invite,
    InviteAlreadyRedeemedError,
    InvalidInviteError,
    UnderageError,
    redeem_invite,
)
from vaeil.domain.vetting import Verdict, VettingModel, vet
from vaeil.domain.pseudonym import (
    InvalidPseudonymError,
    Pseudonym,
    PseudonymAlreadySetError,
    PseudonymDirectory,
    PseudonymTakenError,
)

__all__ = [
    "Applicant",
    "Clock",
    "IdentifierReason",
    "IdentifierScan",
    "FutureDateOfBirthError",
    "Invite",
    "InviteAlreadyRedeemedError",
    "InvalidInviteError",
    "InvalidPseudonymError",
    "Pseudonym",
    "PseudonymAlreadySetError",
    "PseudonymDirectory",
    "PseudonymTakenError",
    "UnderageError",
    "Verdict",
    "VettingModel",
    "redeem_invite",
    "scan_identifiers",
    "vet",
]

from vaeil.domain.identity import (
    MemberIdentity,
    IdentityOwnerMismatchError,
)
from vaeil.domain.self_name import (
    SelfNameMode,
    contains_self_name,
)
from vaeil.domain.profile import (
    RelationshipIntent,
    LifeStage,
    CommunicationStyle,
    PaceAndLifestyle,
    Interest,
    CoreValue,
    ValuesProfile,
    build_values_profile,
    InvalidValuesProfileError,
    ProfileShapeError,
    UnknownProfileChoiceError,
    ProfileSelectionError,
    AboutNormalizationError,
    AboutTooLongError,
    ProfileIdentifierError,
    ProfileSelfNameError,
)
from vaeil.domain.member import (
    Member,
    ConversationRevealState,
    PreRevealMemberView,
    RevealedMemberView,
    OwnProfileView,
    SelfViewerError,
    ViewerNotParticipantError,
    SubjectNotParticipantError,
    InvalidConversationParticipantsError,
    project_member_for_viewer,
    project_own_profile,
    serialize_member_view,
)

__all__ += ['MemberIdentity', 'IdentityOwnerMismatchError', 'SelfNameMode', 'contains_self_name', 'RelationshipIntent', 'LifeStage', 'CommunicationStyle', 'PaceAndLifestyle', 'Interest', 'CoreValue', 'ValuesProfile', 'build_values_profile', 'InvalidValuesProfileError', 'ProfileShapeError', 'UnknownProfileChoiceError', 'ProfileSelectionError', 'AboutNormalizationError', 'AboutTooLongError', 'ProfileIdentifierError', 'ProfileSelfNameError', 'Member', 'ConversationRevealState', 'PreRevealMemberView', 'RevealedMemberView', 'OwnProfileView', 'SelfViewerError', 'ViewerNotParticipantError', 'SubjectNotParticipantError', 'InvalidConversationParticipantsError', 'project_member_for_viewer', 'project_own_profile', 'serialize_member_view']
