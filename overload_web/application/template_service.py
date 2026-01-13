"""Application service for managing templates for order-level record processing."""

from __future__ import annotations

import logging
from typing import Sequence

from overload_web.order_templates.domain import templates

logger = logging.getLogger(__name__)


class OrderTemplateService:
    """Handles order template retrieval and persistence."""

    def __init__(self, repo: templates.SqlRepositoryProtocol) -> None:
        """
        Initialize `OrderTemplateService`.

        Args:
            repo: a `templates.SqlRepositoryProtocol` object.
        """
        self.repo = repo

    def get_template(self, template_id: str) -> templates.OrderTemplate | None:
        """
        Retrieve an order template by its ID.

        Args:
            template_id: unique identifier for the template.

        Returns:
            The retrieved template as a `OrderTemplate` object or None.
        """
        return self.repo.get(id=template_id)

    def list_templates(
        self, offset: int | None = 0, limit: int | None = 20
    ) -> Sequence[templates.OrderTemplate]:
        """
        Retrieve a list of templates in the database.

        Args:
            offset: start position of first `OrderTemplate` object to return.
            limit: the maximum number of `OrderTemplate` objects to return.

        Returns:
            A list of `OrderTemplate` objects.
        """
        return self.repo.list(offset=offset, limit=limit)

    def save_template(
        self, obj: templates.OrderTemplateBase
    ) -> templates.OrderTemplate:
        """
        Save an order template.

        Args:
            obj: the template data as an `OrderTemplateBase` object.

        Raises:
            ValidationError: If the template lacks a name, agent, or primary_matchpoint.

        Returns:
            The saved template as an `OrderTemplate` object.
        """
        save_template = self.repo.save(obj=obj)
        return templates.OrderTemplate(**save_template.model_dump())

    def update_template(
        self, template_id: str, obj: templates.OrderTemplateBase
    ) -> templates.OrderTemplate | None:
        """
        Update an existing order template.

        Args:
            template_id: unique identifier for the template to be updated.
            obj: the data to be replaces as an `OrderTemplateBase` object.

        Returns:
            The updated template as an `OrderTemplate` or None if the template
            does not exist.
        """
        return self.repo.update(id=template_id, data=obj)
