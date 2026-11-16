"""Pure Message policy. The scanner reports reasons; this module decides outcomes."""
from dataclasses import dataclass
from enum import Enum
import unicodedata
from vaeil.domain.conversation import Conversation
from vaeil.domain.identifiers import IdentifierReason, scan_identifiers
from vaeil.domain.vetting import Verdict
from vaeil.domain.privacy import PrivateRecord

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


class MessageConflictError(Exception):
    pass


class MessageNotFoundError(Exception):
    pass


class ReviewState(str, Enum):
    NOT_SUBMITTED = 'not_submitted'
    PENDING = 'pending'
    RELEASED = 'released'
    DISCARDED = 'discarded'


class MessageProvenance(str, Enum):
    NONE = 'none'
    MODEL = 'model'
    HUMAN = 'human'


def message_request_key(value: str) -> str:
    from uuid import UUID
    if not isinstance(value, str):
        raise MessageShapeError('Use a UUID Message request key.')
    try:
        return str(UUID(value))
    except ValueError:
        raise MessageShapeError('Use a UUID Message request key.') from None


_UNSET = object()


class MessageRecord(PrivateRecord):
    # Not a dataclass: asdict must refuse rather than deep-copy the ordinary body.
    __slots__ = ('message_id', 'conversation_id', 'sender_id', 'text', 'request_id',
                 'text_digest', 'assessment', 'created_at', 'delivered_at', 'review_state', 'provenance')

    def __init__(self, message_id, conversation_id, sender_id, text, request_id, assessment,
                 created_at, *, delivered_at=None, review_state=None, provenance=None):
        import hashlib
        from datetime import datetime, timezone
        if any(not isinstance(value, str) or not value for value in (message_id, conversation_id, sender_id)):
            raise MessageShapeError('Use Message, Conversation and sender IDs.')
        body = normalize_message_text(text)
        if not isinstance(assessment, MessageAssessment):
            raise MessageShapeError('Use a typed Message assessment.')
        delivered = assessment.outcome is not MessageOutcome.WITHHELD
        state = review_state if review_state is not None else (ReviewState.PENDING if assessment.reason is ReviewReason.REQUIRED else ReviewState.NOT_SUBMITTED)
        source = provenance if provenance is not None else (MessageProvenance.MODEL if delivered else MessageProvenance.NONE)
        if (not isinstance(created_at, datetime) or created_at.utcoffset() is None
                or not isinstance(state, ReviewState) or not isinstance(source, MessageProvenance)
                or (delivered != (delivered_at is not None))
                or (delivered_at is not None and (not isinstance(delivered_at, datetime) or delivered_at.utcoffset() is None or delivered_at < created_at))
                or (state in {ReviewState.PENDING, ReviewState.DISCARDED} and delivered)
                or (state is ReviewState.RELEASED and (not delivered or source is not MessageProvenance.HUMAN))):
            raise MessageShapeError('Use consistent Message state and aware timestamps.')
        values = dict(message_id=message_id, conversation_id=conversation_id, sender_id=sender_id,
                      text=body, request_id=message_request_key(request_id), text_digest=hashlib.sha256(body.encode('utf-8')).hexdigest(),
                      assessment=assessment, created_at=created_at.astimezone(timezone.utc),
                      delivered_at=None if delivered_at is None else delivered_at.astimezone(timezone.utc), review_state=state, provenance=source)
        for key, value in values.items():
            object.__setattr__(self, key, value)

    def transition(self, *, assessment=None, review_state=None, provenance=None, delivered_at=_UNSET):
        return MessageRecord(self.message_id, self.conversation_id, self.sender_id, self.text, self.request_id,
            assessment if assessment is not None else self.assessment, self.created_at,
            delivered_at=self.delivered_at if delivered_at is _UNSET else delivered_at,
            review_state=self.review_state if review_state is None else review_state,
            provenance=self.provenance if provenance is None else provenance)

    def __setattr__(self, name, value):
        raise AttributeError('Message records are immutable.')

    def __delattr__(self, name):
        raise AttributeError('Message records are immutable.')

    def __repr__(self):
        return '<MessageRecord>'

    __str__ = __repr__

    def __eq__(self, other):
        return type(other) is MessageRecord and all(getattr(self, key) == getattr(other, key) for key in self.__slots__)

    __hash__ = None

    def __reduce__(self):
        from vaeil.domain.privacy import PrivateSerializationError
        raise PrivateSerializationError('Message bodies require explicit authorized mapping.')

    def __reduce_ex__(self, protocol):
        return self.__reduce__()

    def __copy__(self):
        return self.__reduce__()

    def __deepcopy__(self, memo):
        return self.__reduce__()


class MessageReviewDecision(str, Enum):
    RELEASE = 'release'
    DISCARD = 'discard'


@dataclass(frozen=True, slots=True)
class SenderMessageView:
    message_id: str
    conversation_id: str
    outcome: MessageOutcome
    reason: ModerationFailure | ReviewReason | None
    review_state: ReviewState
    identifier_reasons: tuple[IdentifierReason, ...]
    provenance: MessageProvenance
    retry_allowed: bool
    can_submit_for_review: bool
    created_at: object
    delivered_at: object


class DeliveredMessageView(PrivateRecord):
    __slots__ = ('message_id', 'sender_id', 'text', 'delivered_at')

    def __init__(self, message):
        if message.assessment.outcome is MessageOutcome.WITHHELD or message.delivered_at is None:
            raise MessageConflictError('Only delivered Messages have recipient views.')
        for key in self.__slots__:
            object.__setattr__(self, key, getattr(message, key))

    def __setattr__(self, name, value):
        raise AttributeError('Message views are immutable.')

    def __delattr__(self, name):
        raise AttributeError('Message views are immutable.')

    def __repr__(self):
        return '<DeliveredMessageView>'

    __str__ = __repr__


class ReviewMessageView(DeliveredMessageView):
    __slots__ = ('conversation_id', 'identifier_reasons', 'outcome', 'review_state')

    def __init__(self, message):
        for key in ('message_id', 'sender_id', 'text', 'delivered_at', 'conversation_id', 'review_state'):
            object.__setattr__(self, key, getattr(message, key))
        object.__setattr__(self, 'identifier_reasons', message.assessment.identifier_reasons)
        object.__setattr__(self, 'outcome', message.assessment.outcome)

    def __repr__(self):
        return '<ReviewMessageView>'

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class ConversationMessagesView:
    conversation_id: str
    delivered: tuple[DeliveredMessageView, ...]
    attempts: tuple[SenderMessageView, ...]
