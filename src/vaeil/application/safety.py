"""Transactional safety actions; public payloads never include Reporter identity."""
from vaeil.application.admission import SessionPrincipal
from vaeil.domain.authentication import AccessDeniedError, AdmissionStatus, Role
from vaeil.domain.conversation import ConversationNotFoundError, block_conversation
from vaeil.domain.repository import AuditEvent, AuditKind
from vaeil.domain.safety import Report, ReportConflictError, ReportDecision, ReportReason


class SafetyApplication:
    def __init__(self, repository, *, tokens, clock):
        self.repository, self.tokens, self.clock = repository, tokens, clock

    @staticmethod
    def _require(unit, actor, role):
        principal = unit.get_principal(actor.principal_id) if isinstance(actor, SessionPrincipal) else None
        if principal is None or principal.role is not role or principal.admission is not AdmissionStatus.APPROVED:
            raise AccessDeniedError("Access is not permitted.")

    def _pair(self, unit, actor, conversation_id):
        self._require(unit, actor, Role.MEMBER)
        conversation = unit.get_conversation(conversation_id)
        if actor.principal_id not in conversation.participant_ids:
            raise ConversationNotFoundError("Conversation not found.")
        return conversation

    def _audit(self, unit, actor, subject_id, kind, occurred_at):
        unit.append_audit(AuditEvent(self.tokens.new_id(), occurred_at, actor.principal_id, subject_id, kind))

    def block_conversation(self, *, actor, conversation_id):
        with self.repository.transaction() as unit:
            current = self._pair(unit, actor, conversation_id)
            if current.blocked:
                return current
            blocked = block_conversation(current, actor_id=actor.principal_id)
            unit.store_conversation(blocked)
            self._audit(unit, actor, conversation_id, AuditKind.CONVERSATION_BLOCKED, self.clock.now())
            unit.commit()
            return blocked

    def submit_report(self, *, actor, conversation_id, reason: ReportReason):
        if not isinstance(reason, ReportReason):
            raise TypeError("Use a Report reason.")
        with self.repository.transaction() as unit:
            self._pair(unit, actor, conversation_id)
            prior = unit.find_report(conversation_id, actor.principal_id)
            if prior is not None:
                if prior.reason is reason:
                    return prior
                raise ReportConflictError("A Report already exists for this Conversation.")
            now = self.clock.now()
            report = Report(self.tokens.new_id(), conversation_id, actor.principal_id, reason, now)
            unit.add_report(report)
            self._audit(unit, actor, report.report_id, AuditKind.REPORT_SUBMITTED, now)
            unit.commit()
            return report

    def pending_reports(self, *, actor):
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            return unit.list_pending_reports()

    def decide_report(self, *, actor, report_id, decision: ReportDecision):
        if not isinstance(decision, ReportDecision):
            raise TypeError("Use an Admin Report decision.")
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            report = unit.get_report(report_id)
            if report.decision is decision:
                return
            if report.decision is not None:
                raise ReportConflictError("This Report decision is final.")
            unit.set_report_decision(report_id, decision)
            kind = AuditKind.REPORT_APPROVED if decision is ReportDecision.APPROVE else AuditKind.REPORT_REJECTED
            self._audit(unit, actor, report_id, kind, self.clock.now())
            unit.commit()
