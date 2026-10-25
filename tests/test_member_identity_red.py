"""Approved T1 red set. Public seams only; implementation awaits red-test review."""

from collections.abc import Mapping
from dataclasses import FrozenInstanceError, asdict, dataclass, fields, is_dataclass
from datetime import date
from enum import Enum
import copy
import inspect
import json
import pickle
import subprocess
import sys

import pytest

from vaeil import domain as d
from vaeil.domain.privacy import PrivateDate, PrivateText


CANARY_DOB = date(1987, 3, 14)
CANARIES = ("CanaryNameZXQ", "canarylocalzxq@example.invalid", "+919876543210", "1987-03-14")
DOB_FINGERPRINTS = ("1987-03-14", "14/03/1987", "03/14/1987", "14 March 1987",
                    "datetime.date(1987, 3, 14)", "1987, 3, 14")
DOB_PICKLE_STATE = CANARY_DOB.__reduce__()[1][0]


def identity(member_id="subject", *, name=CANARIES[0], email=CANARIES[1], phone=CANARIES[2]):
    return d.MemberIdentity(
        member_id=member_id, legal_name=name, email=email, phone=phone,
        date_of_birth=CANARY_DOB,
    )


def profile(owner=None, **changes):
    owner = owner if owner is not None else identity()
    choices = dict(
        relationship_intent=d.RelationshipIntent.LONG_TERM,
        life_stage=d.LifeStage.UNDERGRADUATE,
        interests=[d.Interest.READING],
        values=[d.CoreValue.HONESTY],
        communication_style=d.CommunicationStyle.DIRECT,
        pace_and_lifestyle=d.PaceAndLifestyle.QUIET_AND_ROUTINE,
        about="",
    )
    choices.update(changes)
    return d.build_values_profile(owner=owner, **choices)


def member(owner=None):
    owner = owner if owner is not None else identity()
    return d.Member(identity=owner, pseudonym=d.Pseudonym("Comet"), values_profile=profile(owner))


def conversation(*, revealed=False, pair=("subject", "viewer"), conversation_id="pair-one"):
    return d.ConversationRevealState(
        conversation_id=conversation_id, participant_ids=pair, revealed=revealed,
    )


def projected(*, revealed=False):
    return d.project_member_for_viewer(
        member(), viewer_id="viewer", conversation=conversation(revealed=revealed),
    )


def assert_no_canary(value):
    text = repr(value)
    # dataclass repr prints date(...) rather than its ISO string.
    for canary in (*CANARIES, *DOB_FINGERPRINTS):
        assert canary not in text
    if isinstance(value, bytes):
        for canary in (*CANARIES, *DOB_FINGERPRINTS):
            assert canary.encode() not in value
        assert DOB_PICKLE_STATE not in value
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            assert pickle.dumps(CANARY_DOB, protocol=protocol) not in value
        try:
            restored = pickle.loads(value)
        except (pickle.UnpicklingError, EOFError, ValueError):
            return
        assert_no_canary(restored)


def inspect_graph(value, *, forbidden_types=()):
    """Probe public payload reachability, including hidden slots, per privacy contract."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (str, int, float, bool, bytes, type(None), date)):
        return value.isoformat() if isinstance(value, date) else value
    assert not isinstance(value, forbidden_types)
    if isinstance(value, Mapping):
        return {key: inspect_graph(item, forbidden_types=forbidden_types) for key, item in value.items()}
    if isinstance(value, (tuple, list, frozenset, set)):
        return [inspect_graph(item, forbidden_types=forbidden_types) for item in value]
    found = {}
    if hasattr(value, "__dict__"):
        found.update({key: inspect_graph(item, forbidden_types=forbidden_types) for key, item in vars(value).items()})
    for cls in type(value).__mro__:
        slots = cls.__dict__.get("__slots__", ())
        slots = (slots,) if isinstance(slots, str) else slots
        for slot in slots:
            if slot not in {"__dict__", "__weakref__"} and hasattr(value, slot):
                found[slot] = inspect_graph(getattr(value, slot), forbidden_types=forbidden_types)
    return found


def test_pre_reveal_type_and_serialized_keys_are_exactly_the_allow_list():
    view = projected()
    assert type(view) is d.PreRevealMemberView
    assert {field.name for field in fields(view)} == {"pseudonym", "values_profile"}
    assert set(d.serialize_member_view(view)) == {"pseudonym", "values_profile"}
    assert view.pseudonym.value == "Comet"
    assert view.values_profile == member().values_profile


@pytest.mark.parametrize("route", [
    "repr", "str", "dict", "slots", "pickle", "pickle-roundtrip", "asdict", "json",
])
def test_private_canaries_are_absent_from_every_pre_reveal_route(route):
    view = projected()
    if route == "repr":
        output = repr(view)
    elif route == "str":
        output = str(view)
    elif route == "dict":
        assert not hasattr(view, "__dict__")
        return  # structural absence, not a vacuous scan of an empty fallback
    elif route == "slots":
        output = inspect_graph(view, forbidden_types=(d.Member, d.MemberIdentity))
    elif route == "pickle":
        raw = pickle.dumps(view)
        assert_no_canary(raw)  # supplementary byte fingerprints
        output = inspect_graph(pickle.loads(raw), forbidden_types=(d.Member, d.MemberIdentity))
    elif route == "pickle-roundtrip":
        restored = pickle.loads(pickle.dumps(view))
        assert restored == view
        output = inspect_graph(restored, forbidden_types=(d.Member, d.MemberIdentity))
    elif route == "asdict":
        output = asdict(view)
    else:
        output = json.dumps(d.serialize_member_view(view), ensure_ascii=False)
    assert_no_canary(output)


def test_serialization_keeps_profile_codes_and_no_private_nested_payload():
    subject = member()
    subject = d.Member(identity=subject.identity, pseudonym=subject.pseudonym, values_profile=profile(
        subject.identity, interests=[d.Interest.READING, d.Interest.ART],
        values=[d.CoreValue.KINDNESS, d.CoreValue.HONESTY],
    ))
    payload = d.serialize_member_view(d.project_member_for_viewer(
        subject, viewer_id="viewer", conversation=conversation(),
    ))
    assert payload == {
        "pseudonym": "Comet",
        "values_profile": {
            "relationship_intent": "long_term", "life_stage": "undergraduate",
            "interests": ["art", "reading"], "values": ["honesty", "kindness"],
            "communication_style": "direct", "pace_and_lifestyle": "quiet_and_routine",
            "about": "",
        },
    }


def test_reveal_adds_identity_without_removing_the_public_profile():
    subject = member()
    view = d.project_member_for_viewer(subject, viewer_id="viewer", conversation=conversation(revealed=True))
    assert type(view) is d.RevealedMemberView
    assert {field.name for field in fields(view)} == {
        "pseudonym", "values_profile", "legal_name", "email", "phone",
    }
    assert view.pseudonym == subject.pseudonym
    assert view.values_profile == subject.values_profile
    assert (view.legal_name, view.email, view.phone) == tuple(PrivateText(value) for value in CANARIES[:3])
    payload = d.serialize_member_view(view)
    assert set(payload) == {"pseudonym", "values_profile", "legal_name", "email", "phone"}
    assert CANARIES[3] not in repr(payload)
    assert "1987, 3, 14" not in repr(payload)


def test_optional_phone_remains_absent_after_reveal_when_not_supplied():
    view = d.project_member_for_viewer(
        member(identity(phone=None)), viewer_id="viewer", conversation=conversation(revealed=True),
    )
    assert view.phone is None
    assert d.serialize_member_view(view)["phone"] is None


def test_reveal_in_one_pair_does_not_reveal_the_subject_in_another():
    subject = member()
    revealed = d.project_member_for_viewer(subject, viewer_id="viewer", conversation=conversation(revealed=True))
    hidden = d.project_member_for_viewer(
        subject, viewer_id="third", conversation=conversation(pair=("subject", "third"), conversation_id="pair-two"),
    )
    assert type(revealed) is d.RevealedMemberView
    assert type(hidden) is d.PreRevealMemberView
    assert_no_canary(d.serialize_member_view(hidden))
    # Check again after the other projection, catching hidden global state/mutation.
    assert type(d.project_member_for_viewer(subject, viewer_id="third", conversation=conversation(
        pair=("subject", "third"), conversation_id="pair-two",
    ))) is d.PreRevealMemberView


@pytest.mark.parametrize("revealed", [False, True], ids=["anonymous", "revealed"])
@pytest.mark.parametrize("case,error_name", [
    ("self", "SelfViewerError"),
    ("outsider", "ViewerNotParticipantError"),
    ("wrong-subject", "SubjectNotParticipantError"),
])
def test_viewer_errors_are_distinct_and_do_not_echo_identity(case, error_name, revealed):
    state = conversation(revealed=revealed)
    viewer_id = "viewer"
    if case == "self":
        viewer_id = "subject"
    elif case == "outsider":
        viewer_id = CANARIES[1]
    else:
        state = conversation(revealed=revealed, pair=("viewer", "third"))
    error_type = getattr(d, error_name)
    with pytest.raises(error_type) as caught:
        d.project_member_for_viewer(member(), viewer_id=viewer_id, conversation=state)
    assert type(caught.value) is error_type
    assert_no_canary(str(caught.value))
    assert_no_canary(repr(caught.value))


@pytest.mark.parametrize("scenario", ["owner-view", "merged-private-owner-repr"])
def test_owner_projection_is_a_separate_redacted_view(scenario):
    view = d.project_own_profile(member())
    assert type(view) is d.OwnProfileView
    assert (view.legal_name, view.email, view.phone) == tuple(PrivateText(value) for value in CANARIES[:3])
    assert view.date_of_birth == PrivateDate(CANARY_DOB)
    assert_no_canary(str(view))
    assert_no_canary(repr(view))


@pytest.mark.parametrize("kind", ["identity", "member", "revealed"])
def test_private_records_never_print_identity_values(kind):
    if kind == "identity":
        value = identity()
    elif kind == "member":
        value = member()
    else:
        value = projected(revealed=True)
    assert_no_canary(repr(value))
    assert_no_canary(str(value))


@pytest.mark.parametrize("kind", ["applicant", "redeemed-invite"])
@pytest.mark.parametrize("surface", ["repr", "str"])
def test_existing_date_of_birth_holders_also_redact_private_representations(kind, surface):
    applicant = d.Applicant(date_of_birth=CANARY_DOB)
    value = applicant if kind == "applicant" else d.Invite(
        code="demo-invite", issuer="admin", redeemed_by=applicant,
    )
    render = repr if surface == "repr" else str
    assert_no_canary(render(value))


@pytest.mark.parametrize("kind", ["identity", "member", "profile", "pre", "post", "own", "conversation"])
def test_approved_records_are_frozen_slotted_and_have_no_photo_field(kind):
    if kind == "identity":
        value = identity()
    elif kind == "member":
        value = member()
    elif kind == "profile":
        value = profile()
    elif kind == "pre":
        value = projected()
    elif kind == "post":
        value = projected(revealed=True)
    elif kind == "own":
        value = d.project_own_profile(member())
    else:
        value = conversation()
    assert is_dataclass(value)
    assert not hasattr(value, "__dict__")
    assert all("photo" not in field.name for field in fields(value))
    for field in fields(value):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field.name, getattr(value, field.name))


def test_member_cannot_supply_a_global_reveal_flag():
    subject = member()
    assert "revealed" not in {field.name for field in fields(subject)}
    assert not hasattr(subject, "revealed")
    with pytest.raises(TypeError):
        d.Member(identity=subject.identity, pseudonym=subject.pseudonym,
                 values_profile=subject.values_profile, revealed=True)
    assert type(d.project_member_for_viewer(subject, viewer_id="viewer", conversation=conversation())) is d.PreRevealMemberView


@pytest.mark.parametrize("enum_name,codes", [
    ("RelationshipIntent", {"long_term", "open_to_relationship", "still_exploring"}),
    ("LifeStage", {"undergraduate", "postgraduate", "working", "between_study_and_work"}),
    ("CommunicationStyle", {"direct", "reflective", "expressive", "balanced"}),
    ("PaceAndLifestyle", {"quiet_and_routine", "balanced_routine_and_spontaneity", "active_and_spontaneous"}),
    ("Interest", {"reading", "music", "films", "gaming", "cooking", "art", "technology", "sports", "fitness", "outdoors", "travel", "volunteering"}),
    ("CoreValue", {"honesty", "kindness", "curiosity", "family", "independence", "ambition", "stability", "creativity", "community", "wellbeing"}),
], ids=["intent", "stage", "communication", "pace", "interests", "values"])
def test_stable_enum_codes_are_the_approved_vocabulary(enum_name, codes):
    enum = getattr(d, enum_name)
    assert {choice.value for choice in enum} == codes


@pytest.mark.parametrize("field_name", ["interests", "values"])
@pytest.mark.parametrize("count,valid", [(0, False), (1, True), (5, True), (6, False)])
def test_complete_profile_selection_boundaries(field_name, count, valid):
    enum = d.Interest if field_name == "interests" else d.CoreValue
    selected = list(enum)[:count]
    if valid:
        saved = profile(**{field_name: selected})
        assert getattr(saved, field_name) == frozenset(selected)
        assert isinstance(getattr(saved, field_name), frozenset)
    else:
        with pytest.raises(d.InvalidValuesProfileError):
            profile(**{field_name: selected})


@pytest.mark.parametrize("field_name", ["interests", "values"])
def test_duplicate_selections_are_refused_before_frozenset_conversion(field_name):
    choice = d.Interest.READING if field_name == "interests" else d.CoreValue.HONESTY
    with pytest.raises(d.InvalidValuesProfileError):
        profile(**{field_name: [choice, choice]})


@pytest.mark.parametrize("field_name", [
    "relationship_intent", "life_stage", "interests", "values", "communication_style", "pace_and_lifestyle",
])
def test_unknown_choice_cannot_be_saved(field_name):
    value = [CANARIES[0]] if field_name in {"interests", "values"} else CANARIES[0]
    with pytest.raises(d.InvalidValuesProfileError) as caught:
        profile(**{field_name: value})
    assert_no_canary(str(caught.value))
    assert_no_canary(repr(caught.value))


def test_about_is_optional_and_normalized_before_storage_and_counting():
    assert profile().about == ""
    assert profile(about="  Ｍｕｓｉｃ  ").about == "Music"
    assert profile(about="  " + "Ａ" * 280 + "  ").about == "A" * 280
    with pytest.raises(d.InvalidValuesProfileError):
        profile(about="Ａ" * 281)


@pytest.mark.parametrize("about,expected", [("", ""), ("   ", ""), ("x" * 279, "x" * 279), ("x" * 280, "x" * 280)], ids=["empty", "blank", "279", "280"])
def test_about_within_the_limit_is_not_truncated_or_rejected(about, expected):
    assert profile(about=about).about == expected


def test_about_normalization_expansion_is_counted_not_raw_length():
    # NFKC maps the ligature to three code points, so 94 raw characters exceed 280.
    with pytest.raises(d.InvalidValuesProfileError):
        profile(about="ﬃ" * 94)
    assert profile(about="ﬃ" * 93).about == "ffi" * 93


@pytest.mark.parametrize("control", ["\x00", "\n", "\r", "\t", "\x1b", "\x7f", "\x85"], ids=["nul", "lf", "cr", "tab", "esc", "del", "c1"])
def test_about_control_characters_are_refused_even_at_trim_boundaries(control):
    with pytest.raises(d.InvalidValuesProfileError):
        profile(about=control + "Music" + control)


@pytest.mark.parametrize("about", [
    "person@example.invalid", "98765 43210", "@someone", "person at example dot com", "https://example.invalid",
    "Contact person@example.invalid",  # retained generated-text input
], ids=["email", "phone", "handle", "obfuscated", "url", "generated-email"])
def test_every_identifier_category_refuses_the_entire_profile_save(about):
    owner = identity()
    before = profile(owner, about="Music")
    with pytest.raises(d.InvalidValuesProfileError) as caught:
        profile(owner, about=about)
    assert about not in str(caught.value)
    assert_no_canary(str(caught.value))
    assert before.about == "Music"
    assert profile(owner, about="Reading").about == "Reading"




@pytest.mark.parametrize("private_text", CANARIES[:3], ids=["legal-name", "email", "phone"])
def test_profile_errors_never_print_private_rejected_text(private_text):
    with pytest.raises(d.InvalidValuesProfileError) as caught:
        profile(about=private_text)
    assert_no_canary(str(caught.value))
    assert_no_canary(repr(caught.value))


def test_about_whole_word_mode_accepts_market_for_mark():
    owner = identity(name="Mark", email="unrelated@example.invalid")
    assert profile(owner, about="I enjoy the market").about == "I enjoy the market"


def test_about_will_false_positive_gives_safe_rephrase_feedback():
    owner = identity(name="Will", email="unrelated@example.invalid")
    with pytest.raises(d.InvalidValuesProfileError) as caught:
        profile(owner, about="I will bring snacks")
    assert caught.value.field == "about"
    assert caught.value.reason == "self_name"
    assert caught.value.can_rephrase is True
    assert "will" not in str(caught.value).casefold()
    assert_no_canary(str(caught.value))


@pytest.mark.parametrize("mode_name,candidate,flagged,owner_name", [
    ("PSEUDONYM", "market", True, "Mark"), ("ABOUT", "market", False, "Mark"),
    ("ABOUT", "MARK", True, "Mark"), ("ABOUT", "Mark, welcome", True, "Mark"),
    ("ABOUT", "bookmark", False, "Mark"), ("PSEUDONYM", "bookmark", True, "Mark"),
    ("ABOUT", "Will.", True, "Will"), ("ABOUT", "will's", True, "Will"),
    ("ABOUT", "willow", False, "Will"),
    ("ABOUT", "STRASSE", True, "Straße"),
    ("PSEUDONYM", "StarSTRASSE", True, "Straße"),
    ("ABOUT", "mark", True, "Ｍａｒｋ"),
    ("ABOUT", "ｍａｒｋ", True, "Mark"),
    ("PSEUDONYM", "Ｍａｒｋ", True, "Mark"),
], ids=["substring", "whole-word", "casefold", "punctuation", "embedded-about", "embedded-name",
        "will-period", "will-apostrophe", "will-embedded", "about-sharp-s", "name-sharp-s", "about-nfkc", "about-input-nfkc", "pseudonym-input-nfkc"])
def test_shared_predicate_has_distinct_pseudonym_and_about_modes(mode_name, candidate, flagged, owner_name):
    owner = identity(name=owner_name, email="unrelated@example.invalid")
    assert d.contains_self_name(candidate, identity=owner, mode=getattr(d.SelfNameMode, mode_name)) is flagged


@pytest.mark.parametrize("name,email,candidate,flagged", [
    ("Ｍａｒｋ", "other@example.invalid", "maRK", True),
    ("Other", "ｍａｒｋ@example.invalid", "MARK", True),
    ("Other", "sara.lee_chen-park+jo@example.invalid", "StarChen", True),
    ("Sara Lee-Chen_Park+Jo", "other@example.invalid", "StarPark", True),
    ("A Li", "xy@example.invalid", "LiStar", False),
    ("Ana", "xy@example.invalid", "StarAna", True),
    ("Other", "local@example.invalid", "Example", False),
    ("Other", "mint+surya@example.invalid", "StarSurya", True),
    ("Other", "mint.surya@example.invalid", "StarSurya", True),
    ("Other", "mint_surya@example.invalid", "StarSurya", True),
    ("Other", "mint-surya@example.invalid", "StarSurya", True),
    ("Nora Arya", "other@example.invalid", "StarArya", True),
    ("Mark", "other@example.invalid", "Markus", True),
    ("ßa", "other@example.invalid", "StarSSA", True),
    ("A\u030An", "other@example.invalid", "ÅnStar", False),
], ids=["nfkc-name", "nfkc-local", "email-separators", "name-separators", "short", "three", "not-domain",
        "plus", "dot", "underscore", "hyphen", "whitespace", "markus", "fold-length-three", "nfkc-length-two"])
def test_self_name_normalization_tokens_and_length_boundary(name, email, candidate, flagged):
    owner = identity(name=name, email=email)
    assert d.contains_self_name(candidate, identity=owner, mode=d.SelfNameMode.PSEUDONYM) is flagged


def test_pseudonym_self_name_failure_does_not_consume_the_slot():
    owner = identity(name="Mark", email="unrelated@example.invalid")
    directory = d.PseudonymDirectory()
    with pytest.raises(d.InvalidPseudonymError) as caught:
        directory.claim("subject", "Market", identity=owner)
    for diagnostic in (str(caught.value), repr(caught.value)):
        assert "mark" not in diagnostic.casefold()
    assert directory.claim("subject", "Comet", identity=owner).value == "Comet"


def test_pseudonym_claim_requires_private_identity_without_a_bypass_default():
    parameter = inspect.signature(d.PseudonymDirectory.claim).parameters["identity"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        d.PseudonymDirectory().claim("subject", "Comet")


def test_claim_rejects_a_mismatched_identity_without_leaking_private_values():
    directory = d.PseudonymDirectory()
    with pytest.raises(d.IdentityOwnerMismatchError) as caught:
        directory.claim("someone-else", "Comet", identity=identity())
    assert_no_canary(str(caught.value))
    assert_no_canary(repr(caught.value))

    assert directory.claim("subject", "Comet", identity=identity()).value == "Comet"

@dataclass(frozen=True, slots=True)
class LeakyCanaryView:
    pseudonym: str = "Comet"
    values_profile: str = "Reading"
    leaked: object = None  # positive-control fake, never a domain implementation


@pytest.mark.parametrize("value", [*CANARIES[:3], CANARY_DOB], ids=["name", "email", "phone", "dob"])
def test_canary_positive_controls_cover_each_private_field(value):
    fake = LeakyCanaryView(leaked=value)
    raw = pickle.dumps(fake)
    payloads = [repr(fake), str(fake), asdict(fake), {"leaked": value},
                inspect_graph(fake), json.dumps(asdict(fake), default=lambda x: x.isoformat()),
                str(ValueError(str(value))), repr(ValueError(str(value))),
                inspect_graph(pickle.loads(raw))]
    for payload in payloads:
        with pytest.raises(AssertionError):
            assert_no_canary(payload)
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        with pytest.raises(AssertionError):
            assert_no_canary(pickle.dumps(fake, protocol=protocol))


def test_clean_canary_control_is_not_rejected():
    assert_no_canary(inspect_graph(LeakyCanaryView()))


@pytest.mark.parametrize("kind", ["member", "identity"])
def test_graph_rejects_even_redacted_private_references(kind):
    private = member() if kind == "member" else identity()
    with pytest.raises(AssertionError):
        inspect_graph(LeakyCanaryView(leaked=private), forbidden_types=(d.Member, d.MemberIdentity))


def test_viewer_error_precedence():
    subject = member()
    other_pair = conversation(pair=("viewer", "third"))
    for viewer in ("subject", "outsider"):
        with pytest.raises(d.SubjectNotParticipantError) as caught:
            d.project_member_for_viewer(subject, viewer_id=viewer, conversation=other_pair)
        assert type(caught.value) is d.SubjectNotParticipantError
    with pytest.raises(d.SelfViewerError) as caught:
        d.project_member_for_viewer(subject, viewer_id="subject", conversation=conversation())
    assert type(caught.value) is d.SelfViewerError
    with pytest.raises(d.ViewerNotParticipantError) as caught:
        d.project_member_for_viewer(subject, viewer_id="outsider", conversation=conversation())
    assert type(caught.value) is d.ViewerNotParticipantError


@pytest.mark.parametrize("pair", [("subject", "subject"), ("subject",), ("subject", "viewer", "third")], ids=["duplicate", "one", "three"])
def test_conversation_state_requires_exactly_two_distinct_participants(pair):
    with pytest.raises(d.InvalidConversationParticipantsError):
        conversation(pair=pair)


@pytest.mark.parametrize("about,expected,valid", [
    ("x" * 281, None, False),
    ("e\u0301" * 280, "é" * 280, True), ("e\u0301" * 281, None, False),
    ("🙂" * 280, "🙂" * 280, True), ("🙂" * 281, None, False),
    ("👍🏽" * 140, "👍🏽" * 140, True), ("👍🏽" * 140 + "x", None, False),
], ids=["ascii281", "combining280", "combining281", "emoji280", "emoji281", "modifier280", "modifier281"])
def test_about_code_point_oracles(about, expected, valid):
    if valid:
        assert profile(about=about).about == expected
    else:
        with pytest.raises(d.InvalidValuesProfileError):
            profile(about=about)


@pytest.mark.parametrize("field_name", ["relationship_intent", "life_stage", "communication_style", "pace_and_lifestyle"])
def test_complete_profile_requires_each_single_choice(field_name):
    for missing in (None, ""):
        with pytest.raises(d.InvalidValuesProfileError):
            profile(**{field_name: missing})


@pytest.mark.parametrize("control", ["\x00", "\n", "\x85"], ids=["nul", "lf", "c1"])
def test_about_rejects_embedded_controls(control):
    with pytest.raises(d.InvalidValuesProfileError):
        profile(about="Mu" + control + "sic")


def test_profile_does_not_retain_mutable_selection_inputs():
    interests = [d.Interest.READING]
    values = [d.CoreValue.HONESTY]
    saved = profile(interests=interests, values=values)
    interests.append(d.Interest.MUSIC)
    values.append(d.CoreValue.KINDNESS)
    assert saved.interests == frozenset({d.Interest.READING})
    assert saved.values == frozenset({d.CoreValue.HONESTY})


@pytest.mark.parametrize("text", ["", "   "] , ids=["empty", "blank"])
def test_whole_word_predicate_handles_empty_input(text):
    assert d.contains_self_name(text, identity=identity(), mode=d.SelfNameMode.ABOUT) is False


def test_whole_word_predicate_is_bounded_on_long_negative_and_late_positive_text():
    code = (
        "from datetime import date; from vaeil import domain as d; "
        "owner=d.MemberIdentity(member_id='one',legal_name='Mark',email='unrelated@example.invalid',phone=None,date_of_birth=date(1998,7,23)); "
        "text='market '*50000; "
        "assert not d.contains_self_name(text,identity=owner,mode=d.SelfNameMode.ABOUT); "
        "assert d.contains_self_name(text+' Mark',identity=owner,mode=d.SelfNameMode.ABOUT)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=3)
    assert result.returncode == 0, result.stderr


class FixedAuditTestClock:
    def today(self):
        return date(2026, 10, 24)


@pytest.mark.parametrize("case,error_name,dob,fingerprints", [
    ("future", "FutureDateOfBirthError", date(2030, 7, 23), ("2030-07-23", "2030, 7, 23")),
    ("underage", "UnderageError", date(2010, 7, 23), ("2010-07-23", "2010, 7, 23")),
    ("invalid", "InvalidInviteError", CANARY_DOB, DOB_FINGERPRINTS),
    ("used", "InviteAlreadyRedeemedError", CANARY_DOB, DOB_FINGERPRINTS),
], ids=["future", "underage", "invalid", "used"])
def test_age_gate_errors_never_echo_dob(case, error_name, dob, fingerprints):
    invite = None if case == "invalid" else d.Invite(code="demo", issuer="admin")
    if case == "used":
        invite.redeemed_by = d.Applicant(date_of_birth=dob)
    error_type = getattr(d, error_name)
    with pytest.raises(error_type) as caught:
        d.redeem_invite(invite=invite, date_of_birth=dob, clock=FixedAuditTestClock())
    assert type(caught.value) is error_type
    for diagnostic in (str(caught.value), repr(caught.value)):
        for fingerprint in fingerprints:
            assert fingerprint not in diagnostic


def test_fixed_once_precedes_other_claim_validation():
    owner = identity()
    directory = d.PseudonymDirectory()
    directory.claim("subject", "Comet", identity=owner)
    with pytest.raises(d.PseudonymAlreadySetError):
        directory.claim("subject", "@bad", identity=identity("wrong-owner"))



@pytest.mark.parametrize("fingerprint", DOB_FINGERPRINTS, ids=["iso", "dmy", "mdy", "english", "date-repr", "date-tuple"])
def test_date_canary_scanner_catches_every_display_form(fingerprint):
    with pytest.raises(AssertionError):
        assert_no_canary(LeakyCanaryView(leaked=fingerprint))


def private_record(kind):
    if kind == "applicant":
        return d.Applicant(date_of_birth=CANARY_DOB)
    if kind == "invite":
        return d.Invite(code="demo", issuer="admin", redeemed_by=d.Applicant(CANARY_DOB))
    if kind == "identity":
        return identity()
    if kind == "member":
        return member()
    if kind == "revealed":
        return projected(revealed=True)
    return d.project_own_profile(member())


@pytest.mark.parametrize("kind", ["applicant", "invite", "identity", "member", "revealed", "own"])
@pytest.mark.parametrize("route", ["pickle", "reduce", "reduce-ex", "copy", "deepcopy", "asdict", "json-asdict", "json-vars"])
def test_private_records_refuse_generic_serialization(kind, route):
    value = private_record(kind)
    protocols = range(pickle.HIGHEST_PROTOCOL + 1) if route == "pickle" else [None]
    for protocol in protocols:
        with pytest.raises(TypeError) as caught:
            if route == "pickle":
                pickle.dumps(value, protocol=protocol)
            elif route == "reduce":
                value.__reduce__()
            elif route == "reduce-ex":
                value.__reduce_ex__(pickle.HIGHEST_PROTOCOL)
            elif route == "copy":
                copy.copy(value)
            elif route == "deepcopy":
                copy.deepcopy(value)
            elif route == "asdict":
                asdict(value)
            else:
                def generic_mapping(obj):
                    assert obj is value, "generic conversion must refuse the private root"
                    return asdict(obj) if route == "json-asdict" else vars(obj)
                json.dumps(value, default=generic_mapping)
        assert str(caught.value).strip(), "refusal must explain the unsupported operation"
        assert_no_canary(str(caught.value))
        assert_no_canary(repr(caught.value))


def test_profile_validation_precedence_is_pinned():
    changes = dict(relationship_intent=42, life_stage="unknown_choice_zxq",
                   interests=[d.Interest.READING, d.Interest.READING],
                   about="\x00" + "x" * 281 + " person@example.invalid " + CANARIES[0])
    stages = [
        (d.ProfileShapeError, {"relationship_intent": d.RelationshipIntent.LONG_TERM}),
        (d.UnknownProfileChoiceError, {"life_stage": d.LifeStage.UNDERGRADUATE}),
        (d.ProfileSelectionError, {"interests": [d.Interest.READING]}),
        (d.AboutNormalizationError, {"about": "x" * 281 + " person@example.invalid " + CANARIES[0]}),
        (d.AboutTooLongError, {"about": "person@example.invalid " + CANARIES[0]}),
        (d.ProfileIdentifierError, {"about": CANARIES[0]}),
        (d.ProfileSelfNameError, {"about": "Music"}),
    ]
    assert len({error for error, _ in stages}) == 7
    for error, fix in stages:
        with pytest.raises(error) as caught:
            profile(**changes)
        assert type(caught.value) is error
        for diagnostic in (str(caught.value), repr(caught.value)):
            assert_no_canary(diagnostic)
            assert "unknown_choice_zxq" not in diagnostic
            assert "x" * 281 not in diagnostic
            assert changes["about"] not in diagnostic
        changes.update(fix)
    assert profile(**changes).about == "Music"
