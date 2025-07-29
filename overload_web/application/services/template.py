"""Application service for managing templates for order-level record processing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence

from overload_web.infrastructure import db

if TYPE_CHECKING:  # pragma: no cover
    from sqlmodel import Session

logger = logging.getLogger(__name__)


class TemplateService:
    """Handles template retrieval and persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize `TemplateService` with a `sqlmodel.Session` object.

        Args:
            session: a `sqlmodel.Session` object.
        """
        self.session = session
        self.repo = db.repository.SqlModelRepository(session=session)

    def get_template(self, template_id: str) -> db.tables.Template | None:
        """
        Retrieve a template by its ID.

        Args:
            template_id: Identifier of the template.

        Returns:
            The retrieved template as a `Template` object or None.
        """
        return self.repo.get(id=template_id)

    def list_templates(
        self, offset: int | None = 0, limit: int | None = 20
    ) -> Sequence[db.tables.Template]:
        """
        Retrieve a list of templates in the database.

        Args:
            offset: start position of `Template` objects to return
            limit: the maximum number of `Template` objects to return

        Returns:
            A list of `Template` objects.
        """
        return self.repo.list(offset=offset, limit=limit)

    def save_template(self, obj: db.tables.Template) -> db.tables.Template:
        """
        Save a template.

        Args:
            data: template data as a dict.

        Raises:
            ValueError: If the template lacks a name or agent.

        Returns:
            The saved template as a dictionary.
        """
        self.repo.save(obj=obj)
        self.session.commit()
        self.session.refresh(obj)

        return obj
