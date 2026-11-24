"""Pure Matching acceptance at the approved ranking seam."""
from dataclasses import replace

from test_repository_contract import example_member
from vaeil.domain.profile import CoreValue, Interest, LifeStage, PaceAndLifestyle


def test_compatibility_example_is_symmetric_and_ignores_about():
    from vaeil.domain.matching import compatibility_score

    left = replace(example_member().values_profile, values=frozenset({CoreValue.HONESTY, CoreValue.KINDNESS}))
    right = replace(left, values=frozenset({CoreValue.HONESTY}), interests=frozenset({Interest.MUSIC}),
                    life_stage=LifeStage.WORKING, pace_and_lifestyle=PaceAndLifestyle.ACTIVE_AND_SPONTANEOUS,
                    about="A completely different free-text profile.")
    assert compatibility_score(left, right) == 5500
    assert compatibility_score(right, left) == 5500
    assert compatibility_score(left, left) == 10000


def test_rank_pairs_breaks_ties_by_canonical_pair_and_excludes_unavailable_members():
    from vaeil.domain.matching import rank_pairs

    profile = example_member().values_profile
    options = dict(excluded_pairs={frozenset({"a", "c"})}, unavailable_ids={"e"})
    expected = [(("a", "b"), 10000), (("a", "d"), 10000), (("b", "c"), 10000), (("b", "d"), 10000), (("c", "d"), 10000)]
    for order in ("edcba", "bdace"):
        actual = rank_pairs({key: profile for key in order}, **options)
        assert [(pair.participant_ids, pair.score) for pair in actual] == expected



def test_rank_uses_descending_score_before_ids_and_rounds_overlap_down():
    from vaeil.domain.matching import rank_pairs

    base = example_member().values_profile
    similar = replace(base, values=frozenset({CoreValue.HONESTY, CoreValue.KINDNESS, CoreValue.FAMILY}),
                      interests=frozenset({Interest.READING, Interest.MUSIC, Interest.ART}))
    distant = replace(base, values=frozenset({CoreValue.STABILITY}), interests=frozenset({Interest.GAMING}))
    pairs = rank_pairs({"a": distant, "c": similar, "b": base}, excluded_pairs=set(), unavailable_ids=set())
    assert [(pair.participant_ids, pair.score) for pair in pairs] == [
        (("b", "c"), 7333), (("a", "b"), 6000), (("a", "c"), 6000),
    ]
