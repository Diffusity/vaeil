"""Pure, pair-scoped eligibility and consent; no storage, clock reads or identity."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from vaeil.domain.conversation import Conversation

MIN_DELIVERED_MESSAGES = 20
MIN_MESSAGES_PER_MEMBER = 5
MIN_ENGAGEMENT_AGE = timedelta(hours=72)


class RevealEvidenceError(Exception):
    """Use validated pair-scoped consent and delivered evidence."""


class RevealActorError(Exception):
    """Only a participant may access this Reveal."""


class RevealBlockedError(Exception):
    """Blocked Conversations cannot change consent."""


class RevealNotEligibleError(Exception):
    """The Engagement Threshold has not been met."""


class RevealCompletedError(Exception):
    """Completed disclosure cannot be withdrawn."""


@dataclass(frozen=True, slots=True)
class DeliveredMessageEvidence:
    message_id: str
    conversation_id: str
    sender_id: str
    delivered_at: datetime


@dataclass(frozen=True, slots=True)
class RevealConsents:
    conversation_id: str
    consented_member_ids: frozenset[str]


@dataclass(frozen=True, slots=True)
class RevealTransition:
    conversation: Conversation
    consents: RevealConsents
    revealed_now: bool


@dataclass(frozen=True, slots=True)
class RevealStatusView:
    conversation_id: str
    eligible: bool
    viewer_consented: bool
    revealed: bool


def _aware(value):
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def is_reveal_eligible(conversation: Conversation, *, delivered: tuple[DeliveredMessageEvidence, ...], now: datetime) -> bool:
    if not isinstance(conversation, Conversation) or not isinstance(delivered, tuple) or not _aware(now):
        raise RevealEvidenceError('Use validated delivered evidence and an aware time.')
    identifiers = set()
    counts = dict.fromkeys(conversation.participant_ids, 0)
    for row in delivered:
        if (not isinstance(row, DeliveredMessageEvidence) or not isinstance(row.message_id, str) or not row.message_id
            or row.message_id in identifiers or row.conversation_id != conversation.conversation_id
            or not isinstance(row.sender_id, str) or row.sender_id not in counts
            or not _aware(row.delivered_at) or row.delivered_at > now):
            raise RevealEvidenceError('Use distinct delivered Messages from this participant pair.')
        identifiers.add(row.message_id)
        counts[row.sender_id] += 1
    return (conversation.active and len(delivered) >= MIN_DELIVERED_MESSAGES
            and all(count >= MIN_MESSAGES_PER_MEMBER for count in counts.values())
            and now - min(row.delivered_at for row in delivered) >= MIN_ENGAGEMENT_AGE)


def change_reveal_consent(conversation: Conversation, *, consents: RevealConsents, actor_id: str,
                          consent: bool, delivered: tuple[DeliveredMessageEvidence, ...], now: datetime) -> RevealTransition:
    eligible = is_reveal_eligible(conversation, delivered=delivered, now=now)
    if (not isinstance(consents, RevealConsents) or consents.conversation_id != conversation.conversation_id
        or not isinstance(consents.consented_member_ids, frozenset)
        or not consents.consented_member_ids.issubset(conversation.participant_ids) or type(consent) is not bool):
        raise RevealEvidenceError('Use valid consent for this Conversation.')
    if actor_id not in conversation.participant_ids:
        raise RevealActorError('Only a participant may change this Reveal.')
    if conversation.blocked:
        raise RevealBlockedError('This Conversation is closed.')
    if conversation.revealed:
        if not consent:
            raise RevealCompletedError('Completed Reveal cannot be withdrawn.')
        return RevealTransition(conversation, consents, False)
    if consent and not eligible:
        raise RevealNotEligibleError('The Engagement Threshold has not been met.')
    identifiers = consents.consented_member_ids | {actor_id} if consent else consents.consented_member_ids - {actor_id}
    updated = RevealConsents(conversation.conversation_id, frozenset(identifiers))
    complete = updated.consented_member_ids == frozenset(conversation.participant_ids)
    return RevealTransition(replace(conversation, revealed=True) if complete else conversation, updated, complete)
