"""Conversation lifecycle through the approved directory and projection seams."""

import pytest
from dataclasses import FrozenInstanceError

from vaeil.domain.conversation import Conversation, ConversationDirectory


def test_member_cannot_open_a_second_active_conversation_and_refusal_is_atomic():
    from vaeil.domain.conversation import (
        ConversationDirectory,
        ConversationNotFoundError,
        MemberAlreadyActiveError,
    )

    directory = ConversationDirectory()
    original = directory.open("ab", participant_ids=("a", "b"))

    with pytest.raises(MemberAlreadyActiveError):
        directory.open("ac", participant_ids=("a", "c"))

    assert directory.get("ab") == original
    with pytest.raises(ConversationNotFoundError):
        directory.get("ac")
    assert directory.open("cd", participant_ids=("c", "d")).participant_ids == ("c", "d")


@pytest.mark.parametrize("revealed,blocked,active,open_for_chat,escalates", [
    (False, False, True, True, True),
    (True, False, False, True, False),
    (False, True, False, False, True),
    (True, True, False, False, False),
])
def test_conversation_lifecycle_is_pair_scoped(revealed, blocked, active, open_for_chat, escalates):
    conversation = Conversation("ab", ("a", "b"), revealed=revealed, blocked=blocked)
    assert conversation.active is active
    assert conversation.open_for_chat is open_for_chat
    assert conversation.identifier_escalation_required is escalates
    state = conversation.reveal_state()
    assert (state.conversation_id, state.participant_ids, state.revealed) == ("ab", ("a", "b"), revealed)
    with pytest.raises(FrozenInstanceError):
        conversation.revealed = not revealed
    assert not hasattr(conversation, "__dict__")


def test_completed_reveal_releases_both_slots_without_closing_chat():
    directory = ConversationDirectory()
    original = directory.open("ab", participant_ids=("a", "b"))
    directory.restore(Conversation("ab", ("a", "b"), revealed=True))
    ac = directory.open("ac", participant_ids=("a", "c"))
    bd = directory.open("bd", participant_ids=("b", "d"))
    assert ac.active and bd.active
    assert directory.get("ab").open_for_chat
    assert not directory.get("ab").identifier_escalation_required
    assert original.active  # earlier snapshots are not mutated


@pytest.mark.parametrize("revealed", [False, True])
@pytest.mark.parametrize("actor", ["a", "b"])
def test_block_closes_chat_frees_slots_and_permanently_excludes_either_pair_order(revealed, actor):
    from vaeil.domain.conversation import PairBlockedError

    directory = ConversationDirectory()
    directory.restore(Conversation("ab", ("a", "b"), revealed=revealed))
    blocked = directory.block("ab", actor_id=actor)
    assert blocked.blocked and not blocked.active and not blocked.open_for_chat
    assert blocked.revealed is revealed
    assert directory.block("ab", actor_id=actor) == blocked
    for pair in [("a", "b"), ("b", "a")]:
        with pytest.raises(PairBlockedError):
            directory.open("again", participant_ids=pair)
    directory.open("ac", participant_ids=("a", "c"))
    directory.open("bd", participant_ids=("b", "d"))
    assert directory.get("ab") == blocked


def test_outsider_block_is_refused_without_state_change():
    from vaeil.domain.conversation import ConversationActorError, MemberAlreadyActiveError

    directory = ConversationDirectory()
    original = directory.open("ab", participant_ids=("a", "b"))
    with pytest.raises(ConversationActorError):
        directory.block("ab", actor_id="outsider-private-canary")
    assert directory.get("ab") == original
    with pytest.raises(MemberAlreadyActiveError):
        directory.open("ac", participant_ids=("a", "c"))


@pytest.mark.parametrize("conversation_id,pair,revealed,blocked", [
    ("", ("a", "b"), False, False),
    (None, ("a", "b"), False, False),
    ([], ("a", "b"), False, False),
    ("ab", ("a", "a"), False, False),
    ("ab", ("a", ""), False, False),
    ("ab", ("a", 2), False, False),
    ("ab", ("a",), False, False),
    ("ab", ("a", "b", "c"), False, False),
    ("ab", ["a", "b"], False, False),
    ("ab", None, False, False),
    ("ab", ("a", "b"), 1, False),
    ("ab", ("a", "b"), False, 0),
], ids=["empty-id", "none-id", "list-id", "same-member", "empty-member", "nonstring-member",
        "short-pair", "long-pair", "mutable-pair", "none-pair", "nonbool-reveal", "nonbool-block"])
def test_conversation_refuses_invalid_shapes_and_flags(conversation_id, pair, revealed, blocked):
    from vaeil.domain.conversation import InvalidConversationError

    with pytest.raises(InvalidConversationError):
        Conversation(conversation_id, pair, revealed=revealed, blocked=blocked)


def test_duplicate_id_cannot_overwrite_or_release_slots():
    from vaeil.domain.conversation import ConversationAlreadyExistsError, MemberAlreadyActiveError

    directory = ConversationDirectory()
    original = directory.open("ab", participant_ids=("a", "b"))
    with pytest.raises(ConversationAlreadyExistsError):
        directory.open("ab", participant_ids=("c", "d"))
    assert directory.get("ab") == original
    with pytest.raises(MemberAlreadyActiveError):
        directory.open("be", participant_ids=("b", "e"))
    assert directory.open("cd", participant_ids=("c", "d")).active


@pytest.mark.parametrize("pair", [("a", "c"), ("c", "a"), ("b", "c"), ("c", "b")])
def test_either_participant_slot_is_checked_in_either_order(pair):
    from vaeil.domain.conversation import MemberAlreadyActiveError

    directory = ConversationDirectory()
    directory.open("ab", participant_ids=("a", "b"))
    with pytest.raises(MemberAlreadyActiveError):
        directory.open("next", participant_ids=pair)


@pytest.mark.parametrize("operation", ["get", "block"])
def test_unknown_conversation_has_a_distinct_safe_error(operation):
    from vaeil.domain.conversation import ConversationNotFoundError

    directory = ConversationDirectory()
    with pytest.raises(ConversationNotFoundError) as caught:
        if operation == "get":
            directory.get("private-canary")
        else:
            directory.block("private-canary", actor_id="actor-canary")
    assert "private-canary" not in str(caught.value)
    assert "actor-canary" not in str(caught.value)


@pytest.mark.parametrize("old,new", [
    (Conversation("ab", ("a", "b"), revealed=True), Conversation("ab", ("a", "b"))),
    (Conversation("ab", ("a", "b"), blocked=True), Conversation("ab", ("a", "b"))),
    (Conversation("ab", ("a", "b")), Conversation("ab", ("a", "c"))),
    (Conversation("ab", ("a", "b")), Conversation("ab", ("b", "a"))),
], ids=["reverse-reveal", "reverse-block", "replace-participant", "reorder-participants"])
def test_restore_cannot_reverse_history_or_change_participants(old, new):
    from vaeil.domain.conversation import InvalidConversationTransitionError

    directory = ConversationDirectory()
    directory.restore(old)
    with pytest.raises(InvalidConversationTransitionError):
        directory.restore(new)
    assert directory.get("ab") == old


def test_restore_cannot_bypass_active_slots_and_failed_restore_consumes_nothing():
    from vaeil.domain.conversation import MemberAlreadyActiveError, ConversationNotFoundError

    directory = ConversationDirectory()
    original = directory.open("ab", participant_ids=("a", "b"))
    with pytest.raises(MemberAlreadyActiveError):
        directory.restore(Conversation("ac", ("a", "c")))
    assert directory.get("ab") == original
    with pytest.raises(ConversationNotFoundError):
        directory.get("ac")
    assert directory.open("cd", participant_ids=("c", "d")).active


@pytest.mark.parametrize("pair", [("a", "b"), ("b", "a")])
@pytest.mark.parametrize("revealed", [False, True])
def test_restore_cannot_bypass_permanent_block(pair, revealed):
    from vaeil.domain.conversation import PairBlockedError, ConversationNotFoundError

    directory = ConversationDirectory()
    directory.restore(Conversation("ab", ("a", "b"), blocked=True))
    with pytest.raises(PairBlockedError):
        directory.restore(Conversation("again", pair, revealed=revealed))
    with pytest.raises(ConversationNotFoundError):
        directory.get("again")
    assert directory.get("ab").blocked


@pytest.mark.parametrize("invalid", [None, {}, "private-canary"])
def test_restore_requires_a_conversation_and_does_not_echo_input(invalid):
    from vaeil.domain.conversation import InvalidConversationError

    with pytest.raises(InvalidConversationError) as caught:
        ConversationDirectory().restore(invalid)
    assert "private-canary" not in str(caught.value)


def test_restore_is_idempotent_and_allows_independent_nonactive_history():
    directory = ConversationDirectory()
    active = directory.open("ac", participant_ids=("a", "c"))
    directory.restore(active)
    revealed = Conversation("ab", ("a", "b"), revealed=True)
    directory.restore(revealed)
    directory.restore(revealed)
    assert directory.get("ac") == active
    assert directory.get("ab") == revealed


def test_directory_reveal_contexts_preserve_identity_isolation_across_sequential_pairs():
    from vaeil.domain import (
        Member, MemberIdentity, Pseudonym, build_values_profile,
        RelationshipIntent, LifeStage, Interest, CoreValue, CommunicationStyle,
        PaceAndLifestyle, project_member_for_viewer, serialize_member_view,
        PreRevealMemberView, RevealedMemberView, SubjectNotParticipantError,
    )
    from datetime import date

    identity = MemberIdentity("a", "PrivateCanaryName", "private-canary@example.invalid", None, date(1987, 3, 14))
    profile = build_values_profile(
        owner=identity, relationship_intent=RelationshipIntent.LONG_TERM,
        life_stage=LifeStage.UNDERGRADUATE, interests=[Interest.READING],
        values=[CoreValue.HONESTY], communication_style=CommunicationStyle.DIRECT,
        pace_and_lifestyle=PaceAndLifestyle.QUIET_AND_ROUTINE, about="",
    )
    member = Member(identity, Pseudonym("Comet"), profile)
    directory = ConversationDirectory()
    directory.open("ab", participant_ids=("a", "b"))
    directory.restore(Conversation("ab", ("a", "b"), revealed=True))
    directory.open("ac", participant_ids=("a", "c"))

    ab, ac = directory.get("ab"), directory.get("ac")
    revealed_view = project_member_for_viewer(member, viewer_id="b", conversation=ab.reveal_state())
    anonymous_view = project_member_for_viewer(member, viewer_id="c", conversation=ac.reveal_state())
    assert type(revealed_view) is RevealedMemberView
    assert type(anonymous_view) is PreRevealMemberView
    assert serialize_member_view(revealed_view)["legal_name"] == "PrivateCanaryName"
    payload = serialize_member_view(anonymous_view)
    assert set(payload) == {"pseudonym", "values_profile"}
    for canary in ("PrivateCanaryName", "private-canary@example.invalid", "1987-03-14"):
        assert canary not in repr(payload)
    assert not ab.identifier_escalation_required
    assert ac.identifier_escalation_required
    outsider = Conversation("de", ("d", "e"))
    with pytest.raises(SubjectNotParticipantError):
        project_member_for_viewer(member, viewer_id="d", conversation=outsider.reveal_state())


def test_pure_reveal_contexts_need_no_active_slot_sequence():
    revealed_ab = Conversation("ab", ("a", "b"), revealed=True)
    anonymous_ac = Conversation("ac", ("a", "c"))
    assert revealed_ab.reveal_state().revealed is True
    assert anonymous_ac.reveal_state().revealed is False
    assert anonymous_ac.identifier_escalation_required


def test_invalid_open_cannot_reserve_an_id_or_slot_and_errors_do_not_echo_input():
    from vaeil.domain.conversation import InvalidConversationError, ConversationActorError

    directory = ConversationDirectory()
    with pytest.raises(InvalidConversationError) as invalid:
        directory.open("private-id-canary", participant_ids=("private-name-canary", "private-name-canary"))
    original = directory.open("private-id-canary", participant_ids=("a", "b"))
    with pytest.raises(ConversationActorError) as outsider:
        directory.block("private-id-canary", actor_id="private-actor-canary")
    assert directory.get("private-id-canary") == original
    for caught in (invalid, outsider):
        for canary in ("private-id-canary", "private-name-canary", "private-actor-canary"):
            assert canary not in str(caught.value)
