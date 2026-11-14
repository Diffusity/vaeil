"""One SQLAlchemy Core implementation for local SQLite and deployed PostgreSQL."""
from contextlib import contextmanager
from datetime import date, datetime
import hashlib
import certifi
from sqlalchemy.engine import make_url
from vaeil.domain.authentication import (PrincipalRecord, ApplicationRecord, Role, AdmissionStatus, AdmissionDecision, AdmissionConflictError, normalize_login_email)

from sqlalchemy import Boolean, Column, DDL, Date, ForeignKey, JSON, MetaData, String, Table, create_engine, event, delete, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from vaeil import domain as d
from vaeil.domain import conversation as c
from vaeil.domain.privacy import PrivateDate, PrivateText
from vaeil.domain.repository import AuditEvent, AuditKind, MemberNotFoundError, RepositoryError, StoredSession, ApplicationConflictError
from vaeil.domain.pseudonym import validate_pseudonym_candidate

metadata = MetaData()
members = Table(
    "members", metadata,
    Column("member_id", String, primary_key=True),
    Column("legal_name", String, nullable=False),
    Column("email", String, nullable=False),
    Column("phone", String),
    Column("date_of_birth", Date, nullable=False),
    Column("pseudonym", String, nullable=False),
    Column("normalized_pseudonym", String, nullable=False, unique=True),
    Column("profile", JSON, nullable=False),
)

conversations = Table(
    "conversations", metadata,
    Column("conversation_id", String, primary_key=True),
    Column("participant_one", String, ForeignKey("members.member_id"), nullable=False),
    Column("participant_two", String, ForeignKey("members.member_id"), nullable=False),
    Column("revealed", Boolean, nullable=False),
    Column("blocked", Boolean, nullable=False),
)

audit_events = Table(
    "audit_events", metadata,
    Column("event_id", String, primary_key=True),
    Column("occurred_at", String, nullable=False),
    Column("actor_id", String),
    Column("subject_id", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("reason_codes", JSON, nullable=False),
)
sessions = Table(
    "server_sessions", metadata,
    Column("token_digest", String, primary_key=True),
    Column("principal_id", String, nullable=False),
    Column("expires_at", String, nullable=False),
)

# Database guards are dialect DDL, not separate repository implementations.
event.listen(audit_events, "after_create", DDL(
    "CREATE TRIGGER audit_no_replace BEFORE INSERT ON audit_events "
    "WHEN EXISTS (SELECT 1 FROM audit_events WHERE event_id = NEW.event_id) "
    "BEGIN SELECT RAISE(ABORT, 'Audit event IDs cannot be replaced.'); END"
).execute_if(dialect="sqlite"))
for operation in ("UPDATE", "DELETE"):
    event.listen(audit_events, "after_create", DDL(
        f"CREATE TRIGGER audit_no_{operation.lower()} BEFORE {operation} ON audit_events "
        "BEGIN SELECT RAISE(ABORT, 'Audit events are append-only.'); END"
    ).execute_if(dialect="sqlite"))
event.listen(audit_events, "after_create", DDL(
    "CREATE FUNCTION vaeil_audit_append_only() RETURNS trigger LANGUAGE plpgsql AS $$ "
    "BEGIN RAISE EXCEPTION 'Audit events are append-only.'; END; $$"
).execute_if(dialect="postgresql"))
event.listen(audit_events, "after_create", DDL(
    "CREATE TRIGGER audit_no_mutation BEFORE UPDATE OR DELETE ON audit_events "
    "FOR EACH ROW EXECUTE FUNCTION vaeil_audit_append_only()"
).execute_if(dialect="postgresql"))
event.listen(audit_events, "after_create", DDL(
    "CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON audit_events "
    "FOR EACH STATEMENT EXECUTE FUNCTION vaeil_audit_append_only()"
).execute_if(dialect="postgresql"))


def row_to_conversation(row) -> c.Conversation:
    return c.Conversation(row["conversation_id"], (row["participant_one"], row["participant_two"]), row["revealed"], row["blocked"])


def encode_private_value(value: PrivateText | PrivateDate) -> str | date:
    """Explicit persistence mapping only; generic private export stays forbidden."""
    if not isinstance(value, (PrivateText, PrivateDate)):
        raise TypeError("Map an opaque private scalar.")
    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()


def member_to_row(member: d.Member) -> dict:
    pseudonym = validate_pseudonym_candidate(member.identity.member_id, member.pseudonym.value, identity=member.identity)
    identity, profile = member.identity, member.values_profile
    return dict(
        member_id=identity.member_id, legal_name=encode_private_value(identity.legal_name),
        email=encode_private_value(identity.email),
        phone=None if identity.phone is None else encode_private_value(identity.phone),
        date_of_birth=encode_private_value(identity.date_of_birth), pseudonym=pseudonym.value, normalized_pseudonym=pseudonym.value.casefold(),
        profile=dict(relationship_intent=profile.relationship_intent.value, life_stage=profile.life_stage.value,
                     interests=sorted(item.value for item in profile.interests),
                     values=sorted(item.value for item in profile.values),
                     communication_style=profile.communication_style.value,
                     pace_and_lifestyle=profile.pace_and_lifestyle.value, about=profile.about),
    )


def row_to_member(row) -> d.Member:
    identity = d.MemberIdentity(row["member_id"], row["legal_name"], row["email"], row["phone"], row["date_of_birth"])
    return d.Member(identity, d.Pseudonym(row["pseudonym"]), d.build_values_profile(owner=identity, **row["profile"]))


class SqlUnitOfWork:
    def __init__(self, connection):
        self._connection = connection
        self._failed = False
        self._committed = False

    def add_member(self, member: d.Member) -> None:
        if self._execute(select(members.c.member_id).where(members.c.member_id == member.identity.member_id)).first():
            raise d.PseudonymAlreadySetError("Pseudonym is fixed once set.")
        self._execute(insert(members).values(**member_to_row(member)))

    def get_member(self, member_id: str) -> d.Member:
        row = self._execute(select(members).where(members.c.member_id == member_id)).mappings().first()
        if row is None:
            raise MemberNotFoundError("Member not found.")
        return row_to_member(row)

    def store_conversation(self, conversation: c.Conversation) -> None:
        existing = tuple(row_to_conversation(row) for row in self._execute(select(conversations)).mappings())
        c.validate_conversation_storage(conversation, existing)
        values = dict(conversation_id=conversation.conversation_id,
                      participant_one=conversation.participant_ids[0], participant_two=conversation.participant_ids[1],
                      revealed=conversation.revealed, blocked=conversation.blocked)
        previous = any(item.conversation_id == conversation.conversation_id for item in existing)
        statement = update(conversations).where(conversations.c.conversation_id == conversation.conversation_id) if previous else insert(conversations)
        self._execute(statement.values(**values))

    def get_conversation(self, conversation_id: str) -> c.Conversation:
        row = self._execute(select(conversations).where(conversations.c.conversation_id == conversation_id)).mappings().first()
        if row is None:
            raise c.ConversationNotFoundError("Conversation not found.")
        return row_to_conversation(row)

    def add_principal(self, principal: PrincipalRecord) -> None:
        if not isinstance(principal, PrincipalRecord):
            raise TypeError("Store a typed principal.")
        identity = principal.identity
        self._execute(insert(principals).values(
            principal_id=identity.member_id, legal_name=encode_private_value(identity.legal_name),
            email=encode_private_value(identity.email), phone=None if identity.phone is None else encode_private_value(identity.phone),
            date_of_birth=encode_private_value(identity.date_of_birth),
            login_email=normalize_login_email(encode_private_value(principal.login_email)),
            password_hash=encode_private_value(principal.password_hash), role=principal.role.value,
            admission=principal.admission.value))

    def get_principal(self, principal_id: str) -> PrincipalRecord | None:
        row = self._execute(select(principals).where(principals.c.principal_id == principal_id)).mappings().first()
        return None if row is None else row_to_principal(row)

    def get_principal_by_email(self, email: str) -> PrincipalRecord | None:
        row = self._execute(select(principals).where(principals.c.login_email == normalize_login_email(email))).mappings().first()
        return None if row is None else row_to_principal(row)

    def add_application(self, application: ApplicationRecord) -> None:
        if not isinstance(application, ApplicationRecord):
            raise TypeError("Store a typed application.")
        self.add_principal(application.principal)
        self._execute(insert(applications).values(principal_id=application.principal.identity.member_id, note=application.note))

    def get_application(self, principal_id: str) -> ApplicationRecord | None:
        principal = self.get_principal(principal_id)
        row = self._execute(select(applications.c.note).where(applications.c.principal_id == principal_id)).first()
        return None if principal is None or row is None else ApplicationRecord(principal, row[0])

    def list_pending_applications(self) -> tuple[ApplicationRecord, ...]:
        ids = self._execute(select(principals.c.principal_id).join(applications).where(
            principals.c.admission == AdmissionStatus.NEEDS_REVIEW.value).order_by(principals.c.principal_id)).scalars()
        return tuple(self.get_application(identifier) for identifier in ids)

    def issue_invite(self, code: str, *, issuer_id: str) -> None:
        if not isinstance(code, str) or not code.strip():
            raise d.InvalidInviteError("Invite is invalid.")
        self._execute(insert(invites).values(code_digest=hashlib.sha256(code.encode()).hexdigest(), issuer_id=issuer_id))

    def require_invite(self, code: str) -> None:
        if not isinstance(code, str):
            raise d.InvalidInviteError("Invite is invalid.")
        key = hashlib.sha256(code.encode()).hexdigest()
        row = self._execute(select(invites.c.redeemed_by).where(invites.c.code_digest == key)).first()
        if row is None:
            raise d.InvalidInviteError("Invite is invalid.")
        if row[0] is not None:
            raise d.InviteAlreadyRedeemedError("Invite is already redeemed.")

    def consume_invite(self, code: str, *, principal_id: str) -> None:
        self.require_invite(code)
        key = hashlib.sha256(code.encode()).hexdigest()
        result = self._execute(update(invites).where(invites.c.code_digest == key, invites.c.redeemed_by.is_(None))
                               .values(redeemed_by=principal_id))
        if result.rowcount != 1:
            raise d.InviteAlreadyRedeemedError("Invite is already redeemed.")

    def set_admission_decision(self, principal_id: str, decision: AdmissionDecision) -> None:
        if not isinstance(decision, AdmissionDecision):
            raise TypeError("Use a human admission decision.")
        approved = decision is AdmissionDecision.APPROVE
        result = self._execute(update(principals).where(principals.c.principal_id == principal_id,
                               principals.c.admission == AdmissionStatus.NEEDS_REVIEW.value,
                               principals.c.role == Role.APPLICANT.value).values(
                                   admission=AdmissionStatus.APPROVED.value if approved else AdmissionStatus.REJECTED.value,
                                   role=Role.MEMBER.value if approved else Role.APPLICANT.value))
        if result.rowcount != 1:
            raise AdmissionConflictError("Application is missing or already decided.")

    def save_onboarding_draft(self, principal_id, draft):
        from vaeil.domain.profile import build_profile_draft, profile_draft_payload
        principal = self.get_principal(principal_id)
        if principal is None:
            raise MemberNotFoundError("Member not found.")
        normalized = build_profile_draft(draft, owner=principal.identity)
        exists = self._execute(select(onboarding.c.principal_id).where(onboarding.c.principal_id == principal_id)).first()
        statement = update(onboarding).where(onboarding.c.principal_id == principal_id) if exists else insert(onboarding)
        self._execute(statement.values(principal_id=principal_id, draft=profile_draft_payload(normalized)))

    def get_onboarding_draft(self, principal_id):
        from vaeil.domain.profile import ProfileDraftInput, build_profile_draft
        principal = self.get_principal(principal_id)
        if principal is None:
            raise MemberNotFoundError("Member not found.")
        row = self._execute(select(onboarding.c.draft).where(onboarding.c.principal_id == principal_id)).first()
        return build_profile_draft(ProfileDraftInput(**({} if row is None else row[0])), owner=principal.identity)

    def update_values_profile(self, member_id, profile):
        previous = self.get_member(member_id)
        member = d.Member(previous.identity, previous.pseudonym, profile)
        self._execute(update(members).where(members.c.member_id == member_id).values(profile=member_to_row(member)["profile"]))

    def append_audit(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            raise TypeError("Append a typed audit event.")
        self._execute(insert(audit_events).values(
            event_id=event.event_id, occurred_at=event.occurred_at.isoformat(), actor_id=event.actor_id,
            subject_id=event.subject_id, kind=event.kind.value,
            reason_codes=[reason.value for reason in event.reason_codes],
        ))

    def list_audit(self, *, subject_id: str) -> tuple[AuditEvent, ...]:
        rows = self._execute(select(audit_events).where(audit_events.c.subject_id == subject_id)
                                       .order_by(audit_events.c.occurred_at, audit_events.c.event_id)).mappings()
        return tuple(AuditEvent(row["event_id"], datetime.fromisoformat(row["occurred_at"]), row["actor_id"],
                                row["subject_id"], AuditKind(row["kind"]),
                                tuple(d.IdentifierReason(reason) for reason in row["reason_codes"])) for row in rows)

    def put_session(self, session: StoredSession) -> None:
        if not isinstance(session, StoredSession):
            raise TypeError("Store a typed server session.")
        digest = encode_private_value(session.token_digest)
        values = dict(token_digest=digest, principal_id=session.principal_id, expires_at=session.expires_at.isoformat())
        result = self._execute(update(sessions).where(sessions.c.token_digest == digest).values(**values))
        if result.rowcount == 0:
            self._execute(insert(sessions).values(**values))

    def get_session(self, token_digest: str) -> StoredSession | None:
        row = self._execute(select(sessions).where(sessions.c.token_digest == token_digest)).mappings().first()
        return None if row is None else StoredSession(row["token_digest"], row["principal_id"], datetime.fromisoformat(row["expires_at"]))

    def delete_session(self, token_digest: str) -> None:
        self._execute(delete(sessions).where(sessions.c.token_digest == token_digest))

    def _execute(self, statement):
        if self._failed or self._committed:
            raise RepositoryError("The transaction is no longer usable.")
        try:
            return self._connection.execute(statement)
        except SQLAlchemyError as error:
            self._failed = True
            original = getattr(error, "orig", None)
            constraint = getattr(getattr(original, "diag", None), "constraint_name", "") or ""
            if isinstance(error, IntegrityError) and (
                "normalized_pseudonym" in constraint or "members.normalized_pseudonym" in str(original)
            ):
                raise d.PseudonymTakenError("Pseudonym is already taken.") from None
            if isinstance(error, IntegrityError) and (
                constraint in {"principals_login_email_key", "principals_pkey"}
                or "principals.login_email" in str(original) or "principals.principal_id" in str(original)
            ):
                raise ApplicationConflictError("Application conflicts with an existing account.") from None
            raise RepositoryError("Repository operation failed.") from None

    def commit(self) -> None:
        if self._failed or self._committed:
            raise RepositoryError("The transaction cannot be committed.")
        try:
            self._connection.commit()
            self._committed = True
        except SQLAlchemyError:
            self._failed = True
            raise RepositoryError("Repository commit failed.") from None


class SqlRepository:
    def __init__(self, engine):
        self._engine = engine

    @contextmanager
    def transaction(self):
        try:
            with self._engine.connect() as connection:
                try:
                    if connection.dialect.name == "postgresql":
                        # Database-scoped transaction lock, shared across app processes.
                        # The small demo serializes repository transactions rather than
                        # risking check/insert races for multi-row Conversation rules.
                        connection.exec_driver_sql("SELECT pg_advisory_xact_lock(843590001)")
                    yield SqlUnitOfWork(connection)
                finally:
                    connection.rollback()
        except SQLAlchemyError:
            raise RepositoryError("Repository operation failed.") from None


@contextmanager
def open_repository(url: str = "sqlite:///vaeil.sqlite"):
    engine = None
    try:
        if url.startswith(("postgresql://", "postgres://")):
            url = "postgresql+psycopg://" + url.split("://", 1)[1]
        try:
            parsed_url = make_url(url)
            connect_args = {}
            if parsed_url.drivername.startswith("postgresql") and parsed_url.host not in {"127.0.0.1", "localhost", "::1"}:
                connect_args = {"sslmode": "verify-full", "sslrootcert": certifi.where(), "connect_timeout": 2,
                                "options": "-c statement_timeout=2000 -c lock_timeout=2000"}
            engine = create_engine(url, echo=False, hide_parameters=True, connect_args=connect_args)
        except (SQLAlchemyError, ValueError, TypeError):
            raise RepositoryError("Repository configuration is invalid.") from None
        if engine.dialect.name == "sqlite":
            @event.listens_for(engine, "connect")
            def configure_sqlite(connection, _):
                connection.isolation_level = None
                connection.execute("PRAGMA foreign_keys=ON")

            @event.listens_for(engine, "begin")
            def begin_sqlite(connection):
                connection.exec_driver_sql("BEGIN IMMEDIATE")
        metadata.create_all(engine)
        yield SqlRepository(engine)
    except SQLAlchemyError:
        raise RepositoryError("Repository unavailable.") from None
    finally:
        if engine is not None:
            engine.dispose()



principals = Table(
    "principals", metadata,
    Column("principal_id", String, primary_key=True),
    Column("legal_name", String, nullable=False), Column("email", String, nullable=False),
    Column("phone", String), Column("date_of_birth", Date, nullable=False),
    Column("login_email", String, nullable=False, unique=True), Column("password_hash", String, nullable=False),
    Column("role", String, nullable=False), Column("admission", String, nullable=False),
)
applications = Table(
    "applications", metadata, Column("principal_id", String, ForeignKey("principals.principal_id"), primary_key=True),
    Column("note", String, nullable=False),
)
invites = Table(
    "invites", metadata, Column("code_digest", String, primary_key=True),
    Column("issuer_id", String, nullable=False), Column("redeemed_by", String),
)


def row_to_principal(row) -> PrincipalRecord:
    identity = d.MemberIdentity(row["principal_id"], row["legal_name"], row["email"], row["phone"], row["date_of_birth"])
    return PrincipalRecord(identity, PrivateText(row["login_email"]), PrivateText(row["password_hash"]),
                           Role(row["role"]), AdmissionStatus(row["admission"]))


onboarding = Table(
    "onboarding_drafts", metadata,
    Column("principal_id", String, ForeignKey("principals.principal_id"), primary_key=True),
    Column("draft", JSON, nullable=False),
)
