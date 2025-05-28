"""
Unit of work pattern for coordinating template-related database operations.

Defines a protocol and concrete implementation that manages the lifecycle of a
`SQLAlchemy` session and encapsulates transaction boundaries.
"""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from overload_web.infrastructure.repositories import repository


@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    """
    A `Protocol` that defines the expected interface for a unit of work that manages
    templates.

    Attributes:
        templates: `RepositoryProtocol` interface for template persistence.

    Methods:
        __enter__: Begins a new transactional context.
        __exit__: Rolls back the transaction and closes the session.
        commit: Commits the transaction.
        rollback: Rolls back the transaction.
    """

    templates: repository.RepositoryProtocol

    def __enter__(self) -> UnitOfWorkProtocol: ...

    def __exit__(self, *args) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


SQL_SESSION_FACTORY = sessionmaker(bind=create_engine("sqlite:///:memory:"))


class OverloadUnitOfWork(UnitOfWorkProtocol):
    """
    Concrete implementation of `UnitOfWorkProtocol` using `SQLAlchemy` for managing
    template persistence.

    Args:
        template_session_factory: `Callable` that returns a new `SQLAlchemy` session.
    """

    def __init__(
        self,
        template_session_factory: Callable = SQL_SESSION_FACTORY,
    ):
        self.template_session_factory = template_session_factory

    def __enter__(self) -> UnitOfWorkProtocol:
        self.template_session = self.template_session_factory()
        self.templates = repository.SqlAlchemyRepository(self.template_session)
        return self

    def __exit__(self, *args):
        self.rollback()
        self.template_session.close()

    def commit(self):
        """Commits the current transation to DB"""
        self.template_session.commit()

    def rollback(self):
        """Rolls back current transaction"""
        self.template_session.rollback()
