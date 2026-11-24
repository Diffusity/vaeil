"""Block and Report decisions use authenticated actors and owned transactions."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ReportReason(str, Enum):
    HARASSMENT = "harassment"
    IDENTITY_PRESSURE = "identity_pressure"
    SCAM = "scam"
    OTHER = "other"


class ReportDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class ReportNotFoundError(Exception):
    """No Report with the requested identifier."""


class ReportConflictError(Exception):
    """A terminal or previous Report choice cannot be changed."""


@dataclass(frozen=True, slots=True)
class Report:
    report_id: str
    conversation_id: str
    reporter_id: str
    reason: ReportReason
    created_at: datetime
    decision: ReportDecision | None = None
