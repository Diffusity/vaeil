"""Authenticated Message orchestration; external moderation never holds a write lock."""
import hashlib
from vaeil.application.admission import SessionPrincipal
from vaeil.domain.authentication import Role, AdmissionStatus, AccessDeniedError
from vaeil.domain.messaging import (
    MessageRecord, MessageOutcome, ModerationFailure, ReviewReason,
    ReviewState, MessageProvenance, MessageReviewDecision, EscalationDecision, SenderMessageView,
    DeliveredMessageView, ReviewMessageView, ConversationMessagesView,
    MessageConflictError, MessageActorError, MessageBlockedError, MessageShapeError,
    normalize_message_text, message_request_key, assess_message,
)
from vaeil.domain.repository import AuditEvent, AuditKind
from vaeil.domain.vetting import Verdict


class MessageApplication:
    def __init__(self, repository, *, tokens, clock, moderator=None):
        self.repository, self.tokens, self.clock, self.moderator = repository, tokens, clock, moderator

    def _require(self, unit, actor, role):
        principal = unit.get_principal(actor.principal_id) if isinstance(actor, SessionPrincipal) else None
        if principal is None or principal.role is not role or principal.admission is not AdmissionStatus.APPROVED:
            raise AccessDeniedError('Access is not permitted.')

    def _pair(self, unit, actor, conversation_id, *, sending=False):
        self._require(unit, actor, Role.MEMBER)
        conversation = unit.get_conversation(conversation_id)
        if actor.principal_id not in conversation.participant_ids:
            raise MessageActorError('Only a participant may access this Conversation.')
        if sending and not conversation.open_for_chat:
            raise MessageBlockedError('This Conversation is closed.')
        return conversation

    @staticmethod
    def _receipt(message, *, processing=False, open_for_chat=True, review_locked=False):
        technical = message.assessment.outcome is MessageOutcome.WITHHELD and isinstance(message.assessment.reason, ModerationFailure)
        retry = technical and message.review_state is ReviewState.NOT_SUBMITTED and open_for_chat and not review_locked
        return SenderMessageView(message.message_id, message.conversation_id, message.assessment.outcome,
            message.assessment.reason, message.review_state, message.assessment.identifier_reasons,
            message.provenance, retry, retry and not processing, message.created_at, message.delivered_at)

    def _moderate(self, text):
        if self.moderator is None:
            return ModerationFailure.UNAVAILABLE
        try:
            result = self.moderator.moderate(text)
            return result if type(result) in {Verdict, ModerationFailure} else ModerationFailure.MALFORMED
        except TimeoutError:
            return ModerationFailure.TIMEOUT
        except OSError:
            return ModerationFailure.UNREACHABLE
        except Exception:
            return ModerationFailure.MALFORMED

    def _event(self, unit, kind, message, actor_id, *, reasons=()):
        unit.append_audit(AuditEvent(self.tokens.new_id(), self.clock.now(), actor_id, message.message_id, kind, reasons))

    def send_message(self, *, actor, conversation_id, request_id, text):
        body, key = normalize_message_text(text), message_request_key(request_id)
        digest = hashlib.sha256(body.encode('utf-8')).hexdigest()
        with self.repository.transaction() as unit:
            conversation = self._pair(unit, actor, conversation_id, sending=True)
            previous = unit.find_message_by_request(conversation_id, actor.principal_id, key)
            if previous is not None:
                if previous.text != body:
                    raise MessageConflictError('This request key already identifies another Message.')
                return self._receipt(previous, processing=unit.message_is_processing(previous.message_id),
                    review_locked=unit.review_text_exists(conversation_id, actor.principal_id, previous.text_digest))
            if unit.review_text_exists(conversation_id, actor.principal_id, digest):
                raise MessageConflictError('This Message text already has a review decision.')
            # Durable in-flight reservation prevents a second process calling moderation.
            pending = assess_message(body, sender_id=actor.principal_id, conversation=conversation, moderation=ModerationFailure.BUSY)
            message = MessageRecord(self.tokens.new_id(), conversation_id, actor.principal_id, body, key, pending, self.clock.now())
            unit.add_message(message, processing=True)
            unit.commit()
        moderation = self._moderate(body)
        with self.repository.transaction() as unit:
            conversation = self._pair(unit, actor, conversation_id, sending=True)
            if unit.review_text_exists(conversation_id, actor.principal_id, digest):
                raise MessageConflictError('This Message text entered review while it was checked.')
            assessment = assess_message(body, sender_id=actor.principal_id, conversation=conversation, moderation=moderation)
            delivered = assessment.outcome is not MessageOutcome.WITHHELD
            finished = message.transition(assessment=assessment,
                review_state=ReviewState.PENDING if assessment.reason is ReviewReason.REQUIRED else ReviewState.NOT_SUBMITTED,
                provenance=MessageProvenance.MODEL if type(moderation) is Verdict else MessageProvenance.NONE,
                delivered_at=self.clock.now() if delivered else None)
            unit.finish_message(finished)
            if assessment.outcome is MessageOutcome.ESCALATED:
                self._event(unit, AuditKind.IDENTIFIER_ESCALATED, finished, actor.principal_id, reasons=assessment.identifier_reasons)
            unit.commit()
        return self._receipt(finished)

    def submit_for_review(self, *, actor, message_id):
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.MEMBER)
            message = unit.get_message(message_id)
            conversation = self._pair(unit, actor, message.conversation_id, sending=True)
            if message.sender_id != actor.principal_id:
                raise MessageActorError('Only the sender may submit this Message for review.')
            if message.review_state is not ReviewState.NOT_SUBMITTED:
                return self._receipt(message, open_for_chat=conversation.open_for_chat)
            if unit.message_is_processing(message_id) or message.assessment.outcome is not MessageOutcome.WITHHELD:
                raise MessageConflictError('This Message cannot be submitted for review.')
            pending = message.transition(review_state=ReviewState.PENDING)
            unit.update_message(pending)
            unit.commit()
        return self._receipt(pending)

    def decide_message(self, *, actor, message_id, decision):
        if not isinstance(decision, MessageReviewDecision):
            raise MessageShapeError('Use a human Message review decision.')
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            message = unit.get_message(message_id)
            if message.review_state is not ReviewState.PENDING or unit.message_is_processing(message_id):
                raise MessageConflictError('Message review has already completed or is unavailable.')
            conversation = unit.get_conversation(message.conversation_id)
            if decision is MessageReviewDecision.RELEASE:
                if not conversation.open_for_chat:
                    raise MessageBlockedError('This Conversation is closed.')
                # Sender/pair authority is rechecked at the moment of release.
                sender = unit.get_principal(message.sender_id)
                if sender is None or sender.role is not Role.MEMBER or sender.admission is not AdmissionStatus.APPROVED:
                    raise AccessDeniedError('Access is not permitted.')
                assessment = assess_message(message.text, sender_id=message.sender_id, conversation=conversation, moderation=Verdict.APPROVED)
                finished = message.transition(assessment=assessment, review_state=ReviewState.RELEASED,
                    provenance=MessageProvenance.HUMAN, delivered_at=self.clock.now())
                kind = AuditKind.MESSAGE_RELEASED
            else:
                finished = message.transition(review_state=ReviewState.DISCARDED, provenance=MessageProvenance.HUMAN)
                kind = AuditKind.MESSAGE_DISCARDED
            unit.update_message(finished)
            self._event(unit, kind, finished, actor.principal_id)
            if finished.assessment.outcome is MessageOutcome.ESCALATED:
                self._event(unit, AuditKind.IDENTIFIER_ESCALATED, finished, actor.principal_id, reasons=finished.assessment.identifier_reasons)
            unit.commit()

    def read_conversation(self, *, actor, conversation_id):
        with self.repository.transaction() as unit:
            conversation = self._pair(unit, actor, conversation_id)
            delivered = tuple(DeliveredMessageView(message) for message in unit.list_delivered_messages(conversation_id))
            attempts = tuple(self._receipt(message, processing=unit.message_is_processing(message.message_id),
                open_for_chat=conversation.open_for_chat,
                review_locked=unit.review_text_exists(conversation_id, actor.principal_id, message.text_digest)) for message in unit.list_sender_messages(conversation_id, actor.principal_id))
            return ConversationMessagesView(conversation_id, delivered, attempts)

    def decide_escalation(self, *, actor, message_id, decision: EscalationDecision) -> None:
        if not isinstance(decision, EscalationDecision):
            raise MessageShapeError("Use an Escalated queue decision.")
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            message = unit.get_message(message_id)
            if message.assessment.outcome is not MessageOutcome.ESCALATED:
                raise MessageConflictError("Message is not Escalated.")
            previous = unit.get_escalation_decision(message_id)
            if previous is decision:
                return
            if previous is not None:
                raise MessageConflictError("Escalated review has already completed.")
            unit.store_escalation_decision(message_id, decision)
            kind = AuditKind.QUEUE_APPROVED if decision is EscalationDecision.APPROVE else AuditKind.QUEUE_REJECTED
            self._event(unit, kind, message, actor.principal_id, reasons=message.assessment.identifier_reasons)
            unit.commit()

    def list_review_messages(self, *, actor):
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            return tuple(ReviewMessageView(unit.get_message(identifier)) for identifier in unit.list_review_message_ids())
