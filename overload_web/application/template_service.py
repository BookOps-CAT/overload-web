"""Application service for managing templates for order-level record processing."""

from __future__ import annotations

import logging
from typing import Sequence

from overload_web.infrastructure import repository, tables

logger = logging.getLogger(__name__)


class OrderTemplateService:
    """Handles order template retrieval and persistence."""

    def __init__(self, session: repository.Session) -> None:
        """
        Initialize `OrderTemplateService` with a `sqlmodel.Session` object.

        Args:
            session: a `sqlmodel.Session` object.
        """
        self.session = session
        self.repo = repository.SqlModelRepository(session=session)

    def get_template(self, template_id: str) -> tables.OrderTemplate | None:
        """
        Retrieve an order template by its ID.

        Args:
            template_id: Identifier of the template.

        Returns:
            The retrieved template as a `OrderTemplate` object or None.
        """
        template = self.repo.get(id=template_id)
        return template

    def list_templates(
        self, offset: int | None = 0, limit: int | None = 20
    ) -> Sequence[tables.OrderTemplate]:
        """
        Retrieve a list of templates in the database.

        Args:
            offset: start position of `OrderTemplate` objects to return
            limit: the maximum number of `OrderTemplate` objects to return

        Returns:
            A list of `OrderTemplate` objects.
        """
        return self.repo.list(offset=offset, limit=limit)

    def save_template(self, obj: tables._OrderTemplateBase) -> tables.OrderTemplate:
        """
        Save an order template.

        Args:
            data: template data as a dict.

        Raises:
            ValueError: If the template lacks a name or agent.

        Returns:
            The saved template.
        """
        valid_obj = tables.OrderTemplate.model_validate(obj)
        self.repo.save(obj=valid_obj)
        self.session.commit()
        self.session.refresh(valid_obj)

        return valid_obj

    def update_template(
        self, template_id: str, obj: tables.OrderTemplateUpdate
    ) -> tables.OrderTemplate | None:
        """
        Update an existing an order template.

        Args:
            data: template data as a dict.

        Raises:
            ValueError: If the template lacks a name or agent.

        Returns:
            The updated template or None if it does not exist
        """
        patch_data = obj.model_dump(exclude_unset=True)
        updated_template = self.repo.update(id=template_id, data=patch_data)
        if updated_template:
            self.session.commit()
            self.session.refresh(updated_template)
        return updated_template
