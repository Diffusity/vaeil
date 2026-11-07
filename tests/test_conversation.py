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
