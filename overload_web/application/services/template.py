"""Application service for managing templates for order-level record processing."""

from __future__ import annotations

import logging
from typing import Any, Optional

from overload_web.domain import models, protocols

logger = logging.getLogger(__name__)


class TemplateService:
    """Handles template retrieval and persistence."""

    def __init__(self, uow: protocols.repositories.UnitOfWorkProtocol) -> None:
        """
        Initialize `TemplateService` with a `UnitOfWorkProtocol` object.

        Args:
            uow: concrete implementation of `UnitOfWorkProtocol` for data access.
        """
        self.uow = uow

    def get_template(self, template_id: str) -> Optional[models.templates.Template]:
        """
        Retrieve a template by its ID.

        Args:
            template_id: Identifier of the template.

        Returns:
            The retrieved template as a `Template` object or None.
        """
        with self.uow:
            return self.uow.templates.get(id=template_id)

    def save_template(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Save a template.

        Args:
            data: template data as a dict.

        Raises:
            ValueError: If the template lacks a name or agent.

        Returns:
            The saved template as a dictionary.
        """
        template = models.templates.Template(**data)

        if not template.name or not template.name.strip():
            raise ValueError("Templates must have a name before being saved.")
        if not template.agent or not template.agent.strip():
            raise ValueError("Templates must have an agent before being saved.")

        with self.uow:
            self.uow.templates.save(obj=template)
            self.uow.commit()

        return template.__dict__
