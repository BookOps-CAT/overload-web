"""Application service for managing templates for order-level record processing."""

from __future__ import annotations

import logging
from typing import Optional, Sequence, TypeVar

from sqlmodel import Session

from overload_web.infrastructure.repositories import repository, tables

logger = logging.getLogger(__name__)
T = TypeVar("T")


class TemplateService:
    """Handles template retrieval and persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize `TemplateService` with a `sqlmodel.Session` object.

        Args:
            session: a `sqlmodel.Session` object.
        """
        self.session = session
        self.repo = repository.SqlModelRepository(session=session)

    def get_template(self, template_id: str) -> Optional[tables.Template]:
        """
        Retrieve a template by its ID.

        Args:
            template_id: Identifier of the template.

        Returns:
            The retrieved template as a `Template` object or None.
        """
        return self.repo.get(id=template_id)

    def list_templates(
        self, offset: Optional[int] = 0, limit: Optional[int] = 20
    ) -> Sequence[tables.Template]:
        """
        Retrieve a list of templates in the database.

        Args:
            offset: start position of `Template` objects to return
            limit: the maximum number of `Template` objects to return

        Returns:
            A list of `Template` objects.
        """
        return self.repo.list(offset=offset, limit=limit)

    def save_template(self, obj: tables.Template) -> tables.Template:
        """
        Save a template.

        Args:
            data: template data as a dict.

        Raises:
            ValueError: If the template lacks a name or agent.

        Returns:
            The saved template as a dictionary.
        """
        if not hasattr(obj, "name") or not obj.name or not obj.name.strip():
            raise ValueError("Templates must have a name before being saved.")
        if not hasattr(obj, "agent") or not obj.agent or not obj.agent.strip():
            raise ValueError("Templates must have an agent before being saved.")

        self.repo.save(obj=obj)
        self.session.commit()
        self.session.refresh(obj)

        return obj
