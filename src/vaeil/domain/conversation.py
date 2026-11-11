"""Pure Conversation lifecycle; persistent atomicity belongs to T5."""

from dataclasses import dataclass, replace
from vaeil.domain.member import ConversationRevealState


class InvalidConversationError(Exception):
    """Use a nonempty ID, distinct participant pair and Boolean state."""


class ConversationAlreadyExistsError(Exception):
    """A Conversation ID cannot be reused by open."""


class ConversationNotFoundError(Exception):
    """The Conversation does not exist in this directory."""


class MemberAlreadyActiveError(Exception):
    """A participant already occupies an active Conversation slot."""


class PairBlockedError(Exception):
    """The pair is permanently excluded after a Block."""


class ConversationActorError(Exception):
    """Only a participant may Block the Conversation."""


class InvalidConversationTransitionError(Exception):
    """History cannot reverse Reveal/Block or replace participants."""


@dataclass(frozen=True, slots=True)
class Conversation:
    conversation_id: str
    participant_ids: tuple[str, str]
    revealed: bool = False
    blocked: bool = False

    def __post_init__(self) -> None:
        pair = self.participant_ids
        if (
            not isinstance(self.conversation_id, str) or not self.conversation_id
            or not isinstance(pair, tuple) or len(pair) != 2
            or any(not isinstance(member, str) or not member for member in pair)
            or pair[0] == pair[1]
            or type(self.revealed) is not bool or type(self.blocked) is not bool
        ):
            raise InvalidConversationError("Use a Conversation ID, distinct Member pair and Boolean state.")

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
        conversation = Conversation(conversation_id, participant_ids)
        if conversation_id in self._conversations:
            raise ConversationAlreadyExistsError("Conversation ID already exists.")
        validate_conversation_storage(conversation, tuple(self._conversations.values()))
        self._conversations[conversation_id] = conversation
        return conversation

    def get(self, conversation_id: str) -> Conversation:
        try:
            return self._conversations[conversation_id]
        except KeyError:
            raise ConversationNotFoundError("Conversation not found.") from None

    def restore(self, conversation: Conversation) -> None:
        """Restore trusted fixtures/state; this is not a public Reveal command."""
        validate_conversation_storage(conversation, tuple(self._conversations.values()))
        self._conversations[conversation.conversation_id] = conversation

    def block(self, conversation_id: str, *, actor_id: str) -> Conversation:
        conversation = self.get(conversation_id)
        if actor_id not in conversation.participant_ids:
            raise ConversationActorError("Only a participant can Block this Conversation.")
        blocked = replace(conversation, blocked=True)
        self._conversations[conversation_id] = blocked
        return blocked


def validate_conversation_storage(conversation: Conversation, existing_conversations: tuple[Conversation, ...]) -> None:
    """Shared T2 placement/monotonic policy; repositories supply an atomic snapshot."""
    if not isinstance(conversation, Conversation):
        raise InvalidConversationError("Restore a validated Conversation.")
    previous = next((item for item in existing_conversations if item.conversation_id == conversation.conversation_id), None)
    if previous is not None and (
        previous.participant_ids != conversation.participant_ids
        or (previous.revealed and not conversation.revealed)
        or (previous.blocked and not conversation.blocked)
    ):
        raise InvalidConversationTransitionError("Conversation history cannot be reversed or reassigned.")
    others = [existing for existing in existing_conversations
              if existing.conversation_id != conversation.conversation_id]
    if any(existing.blocked and frozenset(conversation.participant_ids) == frozenset(existing.participant_ids)
           for existing in others):
        raise PairBlockedError("This pair cannot open another Conversation.")
    if conversation.active and any(
        existing.active and set(conversation.participant_ids).intersection(existing.participant_ids)
        for existing in others
    ):
        raise MemberAlreadyActiveError("A Member already has an active Conversation.")

