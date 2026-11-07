"""Pure Conversation lifecycle; persistent atomicity belongs to T5."""

from dataclasses import dataclass


class ConversationNotFoundError(Exception):
    """The Conversation does not exist in this directory."""


class MemberAlreadyActiveError(Exception):
    """A participant already occupies an active Conversation slot."""


@dataclass(frozen=True, slots=True)
class Conversation:
    conversation_id: str
    participant_ids: tuple[str, str]


class ConversationDirectory:
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    def open(self, conversation_id: str, *, participant_ids: tuple[str, str]) -> Conversation:
        if any(set(participant_ids).intersection(existing.participant_ids)
               for existing in self._conversations.values()):
            raise MemberAlreadyActiveError("A Member already has an active Conversation.")
        conversation = Conversation(conversation_id, participant_ids)
        self._conversations[conversation_id] = conversation
        return conversation

    def get(self, conversation_id: str) -> Conversation:
        try:
            return self._conversations[conversation_id]
        except KeyError:
            raise ConversationNotFoundError("Conversation not found.") from None
