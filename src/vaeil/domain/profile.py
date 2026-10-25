"""Complete structured Values Profiles; every write goes through the factory."""
from dataclasses import dataclass
from enum import Enum
import unicodedata
from vaeil.domain.identifiers import scan_identifiers
from vaeil.domain.identity import MemberIdentity

class RelationshipIntent(str, Enum):
    LONG_TERM = "long_term"
    OPEN_TO_RELATIONSHIP = "open_to_relationship"
    STILL_EXPLORING = "still_exploring"

class LifeStage(str, Enum):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"
    WORKING = "working"
    BETWEEN_STUDY_AND_WORK = "between_study_and_work"

class CommunicationStyle(str, Enum):
    DIRECT = "direct"
    REFLECTIVE = "reflective"
    EXPRESSIVE = "expressive"
    BALANCED = "balanced"

class PaceAndLifestyle(str, Enum):
    QUIET_AND_ROUTINE = "quiet_and_routine"
    BALANCED_ROUTINE_AND_SPONTANEITY = "balanced_routine_and_spontaneity"
    ACTIVE_AND_SPONTANEOUS = "active_and_spontaneous"

class Interest(str, Enum):
    READING = "reading"
    MUSIC = "music"
    FILMS = "films"
    GAMING = "gaming"
    COOKING = "cooking"
    ART = "art"
    TECHNOLOGY = "technology"
    SPORTS = "sports"
    FITNESS = "fitness"
    OUTDOORS = "outdoors"
    TRAVEL = "travel"
    VOLUNTEERING = "volunteering"

class CoreValue(str, Enum):
    HONESTY = "honesty"
    KINDNESS = "kindness"
    CURIOSITY = "curiosity"
    FAMILY = "family"
    INDEPENDENCE = "independence"
    AMBITION = "ambition"
    STABILITY = "stability"
    CREATIVITY = "creativity"
    COMMUNITY = "community"
    WELLBEING = "wellbeing"

MIN_PROFILE_SELECTIONS = 1
MAX_PROFILE_SELECTIONS = 5
MAX_ABOUT_CODE_POINTS = 280

class InvalidValuesProfileError(Exception):
    reason = "invalid_profile"
    message = "Review the profile fields."
    can_rephrase = False

    def __init__(self, *, field="profile"):
        self.field = field
        super().__init__(self.message)

class ProfileShapeError(InvalidValuesProfileError):
    reason = "shape"
    message = "Use the expected profile field types."
class UnknownProfileChoiceError(InvalidValuesProfileError):
    reason = "unknown_choice"
    message = "Choose from the fixed profile options."
class ProfileSelectionError(InvalidValuesProfileError):
    reason = "selection"
    message = "Choose one to five distinct items per list."
class AboutNormalizationError(InvalidValuesProfileError):
    reason = "about_control"
    message = "Remove control characters from About."
class AboutTooLongError(InvalidValuesProfileError):
    reason = "about_length"
    message = "Shorten About to at most 280 code points."
class ProfileIdentifierError(InvalidValuesProfileError):
    reason = "identifier"
    message = "Rephrase About without identifying details."
    can_rephrase = True
class ProfileSelfNameError(InvalidValuesProfileError):
    reason = "self_name"
    message = "Rephrase About without identifying details."
    can_rephrase = True

@dataclass(frozen=True, slots=True)
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
    choices = {
        "relationship_intent": (relationship_intent, RelationshipIntent),
        "life_stage": (life_stage, LifeStage),
        "communication_style": (communication_style, CommunicationStyle),
        "pace_and_lifestyle": (pace_and_lifestyle, PaceAndLifestyle),
    }
    selections = {"interests": (interests, Interest), "values": (values, CoreValue)}
    # All shapes/types precede every code/content check, across all fields.
    if not isinstance(owner, MemberIdentity) or not isinstance(about, str):
        raise ProfileShapeError()
    for name, (value, _) in choices.items():
        if not isinstance(value, str):
            raise ProfileShapeError(field=name)
    for name, (items, _) in selections.items():
        if not isinstance(items, (list, tuple, set, frozenset)) or any(not isinstance(item, str) for item in items):
            raise ProfileShapeError(field=name)
    normalized = {}
    for name, (value, enum) in choices.items():
        try:
            normalized[name] = enum(value)
        except ValueError:
            raise UnknownProfileChoiceError(field=name) from None
    selected = {}
    for name, (items, enum) in selections.items():
        try:
            selected[name] = tuple(enum(item) for item in items)
        except ValueError:
            raise UnknownProfileChoiceError(field=name) from None
    for name, items in selected.items():
        if len(set(items)) != len(items) or not MIN_PROFILE_SELECTIONS <= len(items) <= MAX_PROFILE_SELECTIONS:
            raise ProfileSelectionError(field=name)
    if any(unicodedata.category(char) == "Cc" for char in about):
        raise AboutNormalizationError(field="about")
    text = unicodedata.normalize("NFKC", about).strip()
    if len(text) > MAX_ABOUT_CODE_POINTS:
        raise AboutTooLongError(field="about")
    if scan_identifiers(text).is_flagged:
        raise ProfileIdentifierError(field="about")
    # The next red-green cycle adds the shared self-name seam here.
    return ValuesProfile(**normalized, interests=frozenset(selected["interests"]),
                         values=frozenset(selected["values"]), about=text)
