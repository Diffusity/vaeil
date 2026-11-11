"""Owned transaction boundary; concrete database code belongs in adapters."""
from contextlib import AbstractContextManager
from typing import Protocol

from vaeil.domain.member import Member


class MemberNotFoundError(Exception):
    """The requested Member is absent; no input is echoed."""


class RepositoryError(Exception):
    """An infrastructure operation failed without exposing SQL or private values."""


class UnitOfWork(Protocol):
    def add_member(self, member: Member) -> None: ...
    def get_member(self, member_id: str) -> Member: ...
    def commit(self) -> None: ...


class Repository(Protocol):
    def transaction(self) -> AbstractContextManager[UnitOfWork]: ...
