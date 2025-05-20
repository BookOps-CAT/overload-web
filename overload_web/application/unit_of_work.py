"""
Unit of work pattern for coordinating database operations.

Defines a protocol and concrete implementation that manages the lifecycle of a
`SQLAlchemy` session and encapsulates transaction boundaries.
"""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from overload_web.infrastructure import repository


@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    """
    A `Protocol` that defines the expected interface for a unit of work that manages
    templates.

    Attributes:
        templates: `RepositoryProtocol` interface for template persistence.
        vendor_files: `RepositoryProtocol` interface for file persistence.

    Methods:
        __enter__: Begins a new transactional context.
        __exit__: Rolls back the transaction and closes the session.
        commit: Commits the transaction.
        rollback: Rolls back the transaction.
    """

    templates: repository.RepositoryProtocol
    vendor_files: repository.RepositoryProtocol

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
        session_factory: Callable = SQL_SESSION_FACTORY,
    ):
        self.session_factory = session_factory

    def __enter__(self) -> UnitOfWorkProtocol:
        self.session = self.session_factory()
        self.templates = repository.SqlAlchemyTemplateRepository(self.session)
        self.vendor_files = repository.SqlAlchemyVendorFileRepository(self.session)
        return self

    def __exit__(self, *args):
        self.rollback()
        self.session.close()

    def commit(self):
        """Commits the current transation to DB"""
        self.session.commit()

    def rollback(self):
        """Rolls back current transaction"""
        self.session.rollback()
