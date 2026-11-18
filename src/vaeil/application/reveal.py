"""Authorize and atomically advance pair-scoped Reveal; no public fixture bypass."""
from vaeil.application.admission import SessionPrincipal
from vaeil.domain.authentication import Role, AdmissionStatus, AccessDeniedError
from vaeil.domain.member import project_member_for_viewer
from vaeil.domain.repository import AuditEvent, AuditKind
from vaeil.domain.reveal import (
    DeliveredMessageEvidence, RevealStatusView, RevealActorError,
    is_reveal_eligible, change_reveal_consent,
)


class RevealApplication:
    def __init__(self, repository, *, tokens, clock):
        self.repository, self.tokens, self.clock = repository, tokens, clock

    def _pair(self, unit, actor, conversation_id):
        principal = unit.get_principal(actor.principal_id) if isinstance(actor, SessionPrincipal) else None
        if principal is None or principal.role is not Role.MEMBER or principal.admission is not AdmissionStatus.APPROVED:
            raise AccessDeniedError('Access is not permitted.')
        conversation = unit.get_conversation(conversation_id)
        if actor.principal_id not in conversation.participant_ids:
            raise RevealActorError('Only a participant may access this Reveal.')
        return conversation

    @staticmethod
    def _evidence(unit, conversation_id):
        return tuple(DeliveredMessageEvidence(row.message_id, row.conversation_id, row.sender_id, row.delivered_at)
                     for row in unit.list_delivered_messages(conversation_id))

    @staticmethod
    def _view(conversation, consents, actor, delivered, now):
        return RevealStatusView(conversation.conversation_id,
            is_reveal_eligible(conversation, delivered=delivered, now=now),
            actor.principal_id in consents.consented_member_ids, conversation.revealed)

    def read_reveal(self, *, actor, conversation_id):
        with self.repository.transaction() as unit:
            conversation = self._pair(unit, actor, conversation_id)
            consents = unit.get_reveal_consents(conversation_id)
            return self._view(conversation, consents, actor, self._evidence(unit, conversation_id), self.clock.now())

    def set_reveal_consent(self, *, actor, conversation_id, consent):
        with self.repository.transaction() as unit:
            conversation = self._pair(unit, actor, conversation_id)
            consents = unit.get_reveal_consents(conversation_id)
            delivered, now = self._evidence(unit, conversation_id), self.clock.now()
            changed = change_reveal_consent(conversation, consents=consents, actor_id=actor.principal_id,
                                            consent=consent, delivered=delivered, now=now)
            unit.store_reveal_consents(changed.consents)
            if changed.revealed_now:
                unit.store_conversation(changed.conversation)
                unit.append_audit(AuditEvent(self.tokens.new_id(), now, actor.principal_id,
                                            conversation_id, AuditKind.CONVERSATION_REVEALED))
            unit.commit()
            return self._view(changed.conversation, changed.consents, actor, delivered, now)

    def read_partner(self, *, actor, conversation_id):
        with self.repository.transaction() as unit:
            conversation = self._pair(unit, actor, conversation_id)
            other = next(identifier for identifier in conversation.participant_ids if identifier != actor.principal_id)
            return project_member_for_viewer(unit.get_member(other), viewer_id=actor.principal_id,
                                            conversation=conversation.reveal_state())
