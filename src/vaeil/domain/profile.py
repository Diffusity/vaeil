"""T1 profile seam: deliberately wrong codes/records, unimplemented validation."""
from dataclasses import dataclass
from enum import Enum
from vaeil.domain.identity import MemberIdentity

class RelationshipIntent(str, Enum):
    LONG_TERM = "unimplemented:long_term"
    OPEN_TO_RELATIONSHIP = "unimplemented:open_to_relationship"
    STILL_EXPLORING = "unimplemented:still_exploring"

class LifeStage(str, Enum):
    UNDERGRADUATE = "unimplemented:undergraduate"
    POSTGRADUATE = "unimplemented:postgraduate"
    WORKING = "unimplemented:working"
    BETWEEN_STUDY_AND_WORK = "unimplemented:between_study_and_work"

class CommunicationStyle(str, Enum):
    DIRECT = "unimplemented:direct"
    REFLECTIVE = "unimplemented:reflective"
    EXPRESSIVE = "unimplemented:expressive"
    BALANCED = "unimplemented:balanced"

class PaceAndLifestyle(str, Enum):
    QUIET_AND_ROUTINE = "unimplemented:quiet_and_routine"
    BALANCED_ROUTINE_AND_SPONTANEITY = "unimplemented:balanced_routine_and_spontaneity"
    ACTIVE_AND_SPONTANEOUS = "unimplemented:active_and_spontaneous"

class Interest(str, Enum):
    READING = "unimplemented:reading"
    MUSIC = "unimplemented:music"
    FILMS = "unimplemented:films"
    GAMING = "unimplemented:gaming"
    COOKING = "unimplemented:cooking"
    ART = "unimplemented:art"
    TECHNOLOGY = "unimplemented:technology"
    SPORTS = "unimplemented:sports"
    FITNESS = "unimplemented:fitness"
    OUTDOORS = "unimplemented:outdoors"
    TRAVEL = "unimplemented:travel"
    VOLUNTEERING = "unimplemented:volunteering"

class CoreValue(str, Enum):
    HONESTY = "unimplemented:honesty"
    KINDNESS = "unimplemented:kindness"
    CURIOSITY = "unimplemented:curiosity"
    FAMILY = "unimplemented:family"
    INDEPENDENCE = "unimplemented:independence"
    AMBITION = "unimplemented:ambition"
    STABILITY = "unimplemented:stability"
    CREATIVITY = "unimplemented:creativity"
    COMMUNITY = "unimplemented:community"
    WELLBEING = "unimplemented:wellbeing"

class InvalidValuesProfileError(Exception):
    pass

class ProfileShapeError(InvalidValuesProfileError):
    pass

class UnknownProfileChoiceError(InvalidValuesProfileError):
    pass

class ProfileSelectionError(InvalidValuesProfileError):
    pass

class AboutNormalizationError(InvalidValuesProfileError):
    pass

class AboutTooLongError(InvalidValuesProfileError):
    pass

class ProfileIdentifierError(InvalidValuesProfileError):
    pass

class ProfileSelfNameError(InvalidValuesProfileError):
    pass

@dataclass
class ValuesProfile:
    relationship_intent: RelationshipIntent
    life_stage: LifeStage
    interests: frozenset[Interest]
    values: frozenset[CoreValue]
    communication_style: CommunicationStyle
    pace_and_lifestyle: PaceAndLifestyle
    about: str = ""

def build_values_profile(*, owner: MemberIdentity, relationship_intent, life_stage, interests,
                         values, communication_style, pace_and_lifestyle, about="") -> ValuesProfile:
    raise NotImplementedError("T1 profile validation")
