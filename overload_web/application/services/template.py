"""Application service for managing templates for order-level record processing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence

from overload_web.infrastructure import db

if TYPE_CHECKING:  # pragma: no cover
    from sqlmodel import Session

logger = logging.getLogger(__name__)


class OrderTemplateService:
    """Handles order template retrieval and persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize `OrderTemplateService` with a `sqlmodel.Session` object.

        Args:
            session: a `sqlmodel.Session` object.
        """
        self.session = session
        self.repo = db.repository.SqlModelRepository(session=session)

    def get_template(self, template_id: str) -> db.tables.OrderTemplate | None:
        """
        Retrieve an order template by its ID.

        Args:
            template_id: Identifier of the template.

        Returns:
            The retrieved template as a `OrderTemplate` object or None.
        """
        return self.repo.get(id=template_id)

    def list_templates(
        self, offset: int | None = 0, limit: int | None = 20
    ) -> Sequence[db.tables.OrderTemplate]:
        """
        Retrieve a list of templates in the database.

        Args:
            offset: start position of `OrderTemplate` objects to return
            limit: the maximum number of `OrderTemplate` objects to return

        Returns:
            A list of `OrderTemplate` objects.
        """
        return self.repo.list(offset=offset, limit=limit)

    def save_template(self, obj: db.tables.OrderTemplate) -> db.tables.OrderTemplate:
        """
        Save an order template.

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
