"""
Classes representing a relational database within the domain.

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.

`UnitOfWorkProtocol`
    Defines a unit of work for handling operations within a repository.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K", contravariant=True)


@runtime_checkable
class SqlRepositoryProtocol(Protocol[T, K]):
    """
    Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    def get(self, id: K) -> Optional[T]: ...

    def save(self, obj: T) -> None: ...


@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    """
    A `Protocol` that defines the expected interface for a unit of work that manages
    templates.

    Attributes:
        templates: `SqlRepositoryProtocol` interface for template persistence.

    Methods:
        __enter__: Begins a new transactional context.
        __exit__: Rolls back the transaction and closes the session.
        commit: Commits the transaction.
        rollback: Rolls back the transaction.
    """

    templates: SqlRepositoryProtocol

    def __enter__(self) -> UnitOfWorkProtocol: ...

    def __exit__(self, *args) -> None: ...

    def commit(self) -> None: ...
