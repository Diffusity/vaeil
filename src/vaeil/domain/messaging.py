"""Pure Message policy. The scanner reports reasons; this module decides outcomes."""
from dataclasses import dataclass
from enum import Enum
import unicodedata
from vaeil.domain.conversation import Conversation
from vaeil.domain.identifiers import IdentifierReason, scan_identifiers
from vaeil.domain.vetting import Verdict

MAX_MESSAGE_CODE_POINTS = 2000


class MessageValidationError(Exception):
    pass


class MessageShapeError(MessageValidationError):
    pass


class MessageLengthError(MessageValidationError):
    pass


class MessageControlError(MessageValidationError):
    pass


class MessageActorError(Exception):
    pass


class MessageBlockedError(Exception):
    pass


class MessageOutcome(str, Enum):
    DELIVERED = 'Delivered'
    ESCALATED = 'Escalated'
    WITHHELD = 'Withheld'


class ModerationFailure(str, Enum):
    TIMEOUT = 'timeout'
    UNREACHABLE = 'unreachable'
    BUSY = 'busy'
    QUEUE_FULL = 'queue_full'
    MALFORMED = 'malformed'
    UNAVAILABLE = 'unavailable'


class ReviewReason(str, Enum):
    REQUIRED = 'review_required'


@dataclass(frozen=True, slots=True)
class MessageAssessment:
    outcome: MessageOutcome
    identifier_reasons: tuple[IdentifierReason, ...]
    reason: ModerationFailure | ReviewReason | None = None


def normalize_message_text(text: str) -> str:
    if not isinstance(text, str):
        raise MessageShapeError('Use nonempty Message text.')
    text = unicodedata.normalize('NFKC', text)
    if any(unicodedata.category(char) in {'Cc', 'Cf', 'Cs'} and char not in {'\n', '\t'} for char in text):
        raise MessageControlError('Remove unsupported Message control characters.')
    text = text.strip()
    if not text:
        raise MessageShapeError('Use nonempty Message text.')
    if len(text) > MAX_MESSAGE_CODE_POINTS:
        raise MessageLengthError('Message exceeds the normalized character limit.')
    return text


def assess_message(text: str, *, sender_id: str, conversation: Conversation,
                   moderation: Verdict | ModerationFailure) -> MessageAssessment:
    if not isinstance(conversation, Conversation) or sender_id not in conversation.participant_ids:
        raise MessageActorError('Only a participant may send a Message.')
    if not conversation.open_for_chat:
        raise MessageBlockedError('This Conversation is closed.')
    reasons = scan_identifiers(normalize_message_text(text)).reasons
    if type(moderation) is Verdict and moderation is Verdict.APPROVED:
        outcome = MessageOutcome.ESCALATED if reasons and conversation.identifier_escalation_required else MessageOutcome.DELIVERED
        return MessageAssessment(outcome, reasons)
    reason = ReviewReason.REQUIRED if moderation is Verdict.NEEDS_REVIEW else (
        moderation if type(moderation) is ModerationFailure else ModerationFailure.MALFORMED)
    return MessageAssessment(MessageOutcome.WITHHELD, reasons, reason)
