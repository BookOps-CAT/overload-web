from __future__ import annotations

import abc
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from overload_web.application import object_factories
from overload_web.infrastructure import repository, sierra_adapters


class AbstractUnitOfWork(abc.ABC):
    db_bibs: repository.AbstractRepository
    bibs: sierra_adapters.AbstractService
    bib_factory = object_factories.BibFactory()
    order_factory = object_factories.OrderFactory()
    template_factory = object_factories.TemplateFactory()

    def __enter__(self) -> AbstractUnitOfWork:
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


SQL_SESSION_FACTORY = sessionmaker(bind=create_engine("sqlite:///:memory:"))
SIERRA_SERVICE_FACTORY = sierra_adapters.SierraServiceFactory()


class OverloadUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        library: str,
        sql_factory: Callable = SQL_SESSION_FACTORY,
        sierra_factory: sierra_adapters.SierraServiceFactory = SIERRA_SERVICE_FACTORY,
    ):
        self.sql_factory = sql_factory
        self.sierra_factory = sierra_factory
        self.library = library

    def __enter__(self) -> AbstractUnitOfWork:
        self.session = self.sql_factory()
        self.sierra_session = self.sierra_factory.get_session(library=self.library)
        self.db_bibs = repository.SqlAlchemyRepository(self.session)
        self.bibs = sierra_adapters.SierraService(self.sierra_session())
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
