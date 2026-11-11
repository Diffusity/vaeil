"""One SQLAlchemy Core implementation for local SQLite and deployed PostgreSQL."""
from contextlib import contextmanager
from datetime import date, datetime

from sqlalchemy import Boolean, Column, DDL, Date, ForeignKey, JSON, MetaData, String, Table, create_engine, event, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from vaeil import domain as d
from vaeil.domain import conversation as c
from vaeil.domain.privacy import PrivateDate, PrivateText
from vaeil.domain.repository import AuditEvent, AuditKind, MemberNotFoundError, RepositoryError
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
# Database guards are dialect DDL, not separate repository implementations.
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
        self.connection = connection

    def add_member(self, member: d.Member) -> None:
        if self.connection.execute(select(members.c.member_id).where(members.c.member_id == member.identity.member_id)).first():
            raise d.PseudonymAlreadySetError("Pseudonym is fixed once set.")
        try:
            self.connection.execute(insert(members).values(**member_to_row(member)))
        except IntegrityError as error:
            constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", "") or ""
            if "normalized_pseudonym" in constraint or "members.normalized_pseudonym" in str(error.orig):
                raise d.PseudonymTakenError("Pseudonym is already taken.") from None
            raise RepositoryError("Member could not be stored.") from None

    def get_member(self, member_id: str) -> d.Member:
        row = self.connection.execute(select(members).where(members.c.member_id == member_id)).mappings().first()
        if row is None:
            raise MemberNotFoundError("Member not found.")
        return row_to_member(row)

    def store_conversation(self, conversation: c.Conversation) -> None:
        existing = tuple(row_to_conversation(row) for row in self.connection.execute(select(conversations)).mappings())
        c.validate_conversation_storage(conversation, existing)
        values = dict(conversation_id=conversation.conversation_id,
                      participant_one=conversation.participant_ids[0], participant_two=conversation.participant_ids[1],
                      revealed=conversation.revealed, blocked=conversation.blocked)
        previous = any(item.conversation_id == conversation.conversation_id for item in existing)
        statement = update(conversations).where(conversations.c.conversation_id == conversation.conversation_id) if previous else insert(conversations)
        self.connection.execute(statement.values(**values))

    def get_conversation(self, conversation_id: str) -> c.Conversation:
        row = self.connection.execute(select(conversations).where(conversations.c.conversation_id == conversation_id)).mappings().first()
        if row is None:
            raise c.ConversationNotFoundError("Conversation not found.")
        return row_to_conversation(row)

    def append_audit(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            raise TypeError("Append a typed audit event.")
        self.connection.execute(insert(audit_events).values(
            event_id=event.event_id, occurred_at=event.occurred_at.isoformat(), actor_id=event.actor_id,
            subject_id=event.subject_id, kind=event.kind.value,
            reason_codes=[reason.value for reason in event.reason_codes],
        ))

    def list_audit(self, *, subject_id: str) -> tuple[AuditEvent, ...]:
        rows = self.connection.execute(select(audit_events).where(audit_events.c.subject_id == subject_id)
                                       .order_by(audit_events.c.occurred_at, audit_events.c.event_id)).mappings()
        return tuple(AuditEvent(row["event_id"], datetime.fromisoformat(row["occurred_at"]), row["actor_id"],
                                row["subject_id"], AuditKind(row["kind"]),
                                tuple(d.IdentifierReason(reason) for reason in row["reason_codes"])) for row in rows)

    def commit(self) -> None:
        self.connection.commit()


class SqlRepository:
    def __init__(self, engine):
        self.engine = engine

    @contextmanager
    def transaction(self):
        try:
            with self.engine.connect() as connection:
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
def open_repository(url: str):
    engine = None
    try:
        if url.startswith(("postgresql://", "postgres://")):
            url = "postgresql+psycopg://" + url.split("://", 1)[1]
        engine = create_engine(url, echo=False, hide_parameters=True)
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
