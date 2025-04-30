from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from overload_web.infrastructure import repository


@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    templates: repository.RepositoryProtocol

    def __enter__(self) -> UnitOfWorkProtocol: ...

    def __exit__(self, *args) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


SQL_SESSION_FACTORY = sessionmaker(bind=create_engine("sqlite:///:memory:"))


class OverloadUnitOfWork(UnitOfWorkProtocol):
    def __init__(self, session_factory: Callable = SQL_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self) -> UnitOfWorkProtocol:
        self.session = self.session_factory()
        self.templates = repository.SqlAlchemyRepository(self.session)
        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
