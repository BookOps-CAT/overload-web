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
        self.template_session.commit()

    def rollback(self):
        self.template_session.rollback()
