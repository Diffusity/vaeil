"""Pure Conversation lifecycle; persistent atomicity belongs to T5."""

from dataclasses import dataclass
from vaeil.domain.member import ConversationRevealState


class ConversationNotFoundError(Exception):
    """The Conversation does not exist in this directory."""


class MemberAlreadyActiveError(Exception):
    """A participant already occupies an active Conversation slot."""


@dataclass(frozen=True, slots=True)
class Conversation:
    conversation_id: str
    participant_ids: tuple[str, str]
    revealed: bool = False
    blocked: bool = False

    @property
    def active(self) -> bool:
        return not self.revealed and not self.blocked

    @property
    def open_for_chat(self) -> bool:
        return not self.blocked

    @property
    def identifier_escalation_required(self) -> bool:
        return not self.revealed

    def reveal_state(self) -> ConversationRevealState:
        return ConversationRevealState(self.conversation_id, self.participant_ids, self.revealed)


class ConversationDirectory:
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    def open(self, conversation_id: str, *, participant_ids: tuple[str, str]) -> Conversation:
        if any(existing.active and set(participant_ids).intersection(existing.participant_ids)
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

    def restore(self, conversation: Conversation) -> None:
        """Restore trusted fixtures/state; this is not a public Reveal command."""
        self._conversations[conversation.conversation_id] = conversation
