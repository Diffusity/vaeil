"""One SQLAlchemy Core implementation for local SQLite and deployed PostgreSQL."""
from contextlib import contextmanager
from datetime import date

from sqlalchemy import Column, Date, JSON, MetaData, String, Table, create_engine, insert, select
from sqlalchemy.exc import SQLAlchemyError

from vaeil import domain as d
from vaeil.domain.privacy import PrivateDate, PrivateText
from vaeil.domain.repository import MemberNotFoundError, RepositoryError

metadata = MetaData()
members = Table(
    "members", metadata,
    Column("member_id", String, primary_key=True),
    Column("legal_name", String, nullable=False),
    Column("email", String, nullable=False),
    Column("phone", String),
    Column("date_of_birth", Date, nullable=False),
    Column("pseudonym", String, nullable=False),
    Column("profile", JSON, nullable=False),
)


def encode_private_value(value: PrivateText | PrivateDate) -> str | date:
    """Explicit persistence mapping only; generic private export stays forbidden."""
    if not isinstance(value, (PrivateText, PrivateDate)):
        raise TypeError("Map an opaque private scalar.")
    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()


def member_to_row(member: d.Member) -> dict:
    identity, profile = member.identity, member.values_profile
    return dict(
        member_id=identity.member_id, legal_name=encode_private_value(identity.legal_name),
        email=encode_private_value(identity.email),
        phone=None if identity.phone is None else encode_private_value(identity.phone),
        date_of_birth=encode_private_value(identity.date_of_birth), pseudonym=member.pseudonym.value,
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
        self.connection.execute(insert(members).values(**member_to_row(member)))

    def get_member(self, member_id: str) -> d.Member:
        row = self.connection.execute(select(members).where(members.c.member_id == member_id)).mappings().first()
        if row is None:
            raise MemberNotFoundError("Member not found.")
        return row_to_member(row)

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
        metadata.create_all(engine)
        yield SqlRepository(engine)
    except SQLAlchemyError:
        raise RepositoryError("Repository unavailable.") from None
    finally:
        if engine is not None:
            engine.dispose()
