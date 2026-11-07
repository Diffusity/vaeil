"""Conversation lifecycle through the approved directory and projection seams."""

import pytest


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
