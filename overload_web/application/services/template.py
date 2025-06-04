"""
Unit of work pattern for coordinating template-related database operations.

Defines a protocol and concrete implementation that manages the lifecycle of a
`SQLAlchemy` session and encapsulates transaction boundaries.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from overload_web.domain.models import templates
from overload_web.domain.protocols import repositories
from overload_web.infrastructure.repositories import repository

logger = logging.getLogger(__name__)

SQL_SESSION_FACTORY = sessionmaker(bind=create_engine("sqlite:///:memory:"))


class OverloadUnitOfWork:
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
        self.templates: repositories.SqlRepositoryProtocol
        self.template_session_factory = template_session_factory

    def __enter__(self) -> repositories.UnitOfWorkProtocol:
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


class TemplateService:
    def __init__(self, uow: repositories.UnitOfWorkProtocol) -> None:
        self.uow = uow

    def get_template(self, template_id: str) -> Optional[templates.Template]:
        with self.uow:
            return self.uow.templates.get(id=template_id)

    def save_template(self, data: dict[str, Any]) -> dict[str, Any]:
        template = templates.Template(**data)

        if not template.name or not template.name.strip():
            raise ValueError("Templates must have a name before being saved.")
        if not template.agent or not template.agent.strip():
            raise ValueError("Templates must have an agent before being saved.")

        with self.uow:
            self.uow.templates.save(obj=template)
            self.uow.commit()

        return template.__dict__
