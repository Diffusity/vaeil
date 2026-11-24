"""Deterministic values-only ranking and immutable bilateral Match decisions."""
from dataclasses import dataclass
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
