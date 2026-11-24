"""Deterministic values-only ranking and immutable bilateral Match decisions."""
from dataclasses import dataclass, replace
from enum import Enum
from itertools import combinations

from vaeil.domain.profile import ValuesProfile


def compatibility_score(left: ValuesProfile, right: ValuesProfile) -> int:
    comparisons = ((25, left.relationship_intent, right.relationship_intent),
                   (15, left.communication_style, right.communication_style),
                   (15, left.pace_and_lifestyle, right.pace_and_lifestyle),
                   (5, left.life_stage, right.life_stage))
    sets = ((30, left.values, right.values), (10, left.interests, right.interests))
    return (sum(weight * 100 for weight, a, b in comparisons if a == b)
            + sum(weight * 100 * len(a & b) // len(a | b) for weight, a, b in sets))


@dataclass(frozen=True, slots=True)
class RankedPair:
    participant_ids: tuple[str, str]
    score: int


def rank_pairs(profiles_by_member_id, *, excluded_pairs, unavailable_ids) -> tuple[RankedPair, ...]:
    available = sorted(profiles_by_member_id.keys() - unavailable_ids)
    candidates = (
        RankedPair((a, b), compatibility_score(profiles_by_member_id[a], profiles_by_member_id[b]))
        for a, b in combinations(available, 2) if frozenset({a, b}) not in excluded_pairs
    )
    return tuple(sorted(candidates, key=lambda pair: (-pair.score, pair.participant_ids)))


class MatchDecision(str, Enum):
    ACCEPT = "accept"
    DECLINE = "decline"


class MatchNotFoundError(Exception):
    """Hide absent matches and matches outside the participant pair."""


class MatchConflictError(Exception):
    """The requested decision is no longer compatible with current state."""


@dataclass(frozen=True, slots=True)
class Match:
    match_id: str
    participant_ids: tuple[str, str]
    decisions: tuple[MatchDecision | None, MatchDecision | None] = (None, None)
    conversation_id: str | None = None

    def participant_index(self, member_id: str) -> int:
        if member_id not in self.participant_ids:
            raise MatchNotFoundError("Match not found.")
        return self.participant_ids.index(member_id)

    @property
    def state(self) -> str:
        if self.conversation_id is not None:
            return "accepted"
        if MatchDecision.DECLINE in self.decisions:
            return "declined"
        return "pending"

    def record_decision(self, member_id: str, decision: MatchDecision) -> "Match":
        index = self.participant_index(member_id)
        if not isinstance(decision, MatchDecision):
            raise TypeError("Use a Match decision.")
        previous = self.decisions[index]
        if previous is decision:
            return self
        if previous is not None or self.state != "pending":
            raise MatchConflictError("This Match decision cannot be changed.")
        choices = (decision, self.decisions[1]) if index == 0 else (self.decisions[0], decision)
        return replace(self, decisions=choices)
