"""Owned transaction boundary; concrete database code belongs in adapters."""
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from vaeil.domain.identifiers import IdentifierReason
from typing import Protocol

from vaeil.domain.member import Member
from vaeil.domain.conversation import Conversation


class MemberNotFoundError(Exception):
    """The requested Member is absent; no input is echoed."""


class RepositoryError(Exception):
    """An infrastructure operation failed without exposing SQL or private values."""


class AuditKind(str, Enum):
    INVITE_REDEEMED = "invite_redeemed"
    VETTING_APPROVED = "vetting_approved"
    VETTING_NEEDS_REVIEW = "vetting_needs_review"
    IDENTIFIER_ESCALATED = "identifier_escalated"
    CONVERSATION_REVEALED = "conversation_revealed"
    CONVERSATION_BLOCKED = "conversation_blocked"
    REPORT_SUBMITTED = "report_submitted"
    ADMISSION_APPROVED = "admission_approved"
    ADMISSION_REJECTED = "admission_rejected"
    QUEUE_APPROVED = "queue_approved"
    QUEUE_REJECTED = "queue_rejected"
    MESSAGE_RELEASED = "message_released"
    MESSAGE_DISCARDED = "message_discarded"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    occurred_at: datetime
    actor_id: str | None
    subject_id: str
    kind: AuditKind
    reason_codes: tuple[IdentifierReason, ...] = ()

    def __post_init__(self):
        if (not isinstance(self.event_id, str) or not self.event_id
                or not isinstance(self.subject_id, str) or not self.subject_id
                or (self.actor_id is not None and (not isinstance(self.actor_id, str) or not self.actor_id))
                or not isinstance(self.occurred_at, datetime) or self.occurred_at.utcoffset() is None
                or not isinstance(self.kind, AuditKind) or not isinstance(self.reason_codes, tuple)
                or any(not isinstance(reason, IdentifierReason) for reason in self.reason_codes)):
            raise TypeError("Use typed audit metadata, aware time and enum reason codes.")
        object.__setattr__(self, "occurred_at", self.occurred_at.astimezone(timezone.utc))


class UnitOfWork(Protocol):
    def add_member(self, member: Member) -> None: ...
    def get_member(self, member_id: str) -> Member: ...
    def store_conversation(self, conversation: Conversation) -> None: ...
    def get_conversation(self, conversation_id: str) -> Conversation: ...
    def append_audit(self, event: AuditEvent) -> None: ...
    def list_audit(self, *, subject_id: str) -> tuple[AuditEvent, ...]: ...
    def commit(self) -> None: ...


class Repository(Protocol):
    def transaction(self) -> AbstractContextManager[UnitOfWork]: ...
