"""A class representing a relational database for `TemplateTable` objects.

Classes:

`SqlModelRepository`
    `SQLModel` implementation of `SqlRepositoryProtocol` for managing
    `TemplateTable` objects in a SQL database.
"""

from __future__ import annotations

import logging
from typing import Sequence

from sqlmodel import Session, select

from overload_web.domain.models import templates
from overload_web.infrastructure.db import tables

logger = logging.getLogger(__name__)


class SqlModelRepository:
    """
    `SQLModel` repository for `TemplateTable` objects.

    This class is a concrete implementation of the `SqlRepositoryProtocol` protocol.

    Args:
        session: a `sqlmodel.Session`.
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str | int) -> templates.OrderTemplate | None:
        """
        Retrieve a `OrderTemplate` object by its ID.

        Args:
            id: the primary key of the `OrderTemplate`.

        Returns:
            a `OrderTemplate` instance or `None` if not found.
        """
        template = self.session.get(tables.TemplateTable, id)
        return templates.OrderTemplate(**template.model_dump()) if template else None

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[templates.OrderTemplate]:
        """
        Retrieve all `OrderTemplate` objects in the database.

        Args:
            offset: start position of `OrderTemplate` objects to return
            limit: the maximum number of `OrderTemplate` objects to return

        Returns:
            a sequence of `OrderTemplate` objects.
        """
        statement = select(tables.TemplateTable).offset(offset).limit(limit)
        results = self.session.exec(statement)
        all_templates = results.all()
        return [templates.OrderTemplate(**i.model_dump()) for i in all_templates]

    def save(self, obj: tables.TemplateTable) -> tables.TemplateTable:
        """
        Adds a new `TemplateTable` to the database.

        Args:
            obj: the `TemplateTable` object to save.
        """
        valid_obj = tables.TemplateTable.model_validate(obj, from_attributes=True)
        self.session.add(valid_obj)
        self.session.commit()
        self.session.refresh(valid_obj)
        return valid_obj

    def apply_updates(
        self, id: str, data: tables.SQLModel
    ) -> templates.OrderTemplate | None:
        """
        Updates an existing `OrderTemplate` in the database.

        Args:
            id: the id of the template to be updated
            data: the data to be used to update the existing template.
        Returns:
            a `TemplateTable` instance or `None` if not found.
        """
        template = self.session.get(tables.TemplateTable, id)
        if not template:
            logger.error(f"Template '{id}' does not exist")
        else:
            patch_data = data.model_dump(exclude_unset=True)
            template.sqlmodel_update(patch_data)
            self.session.add(template)
            self.session.commit()
            self.session.refresh(template)
        return templates.OrderTemplate(**template.model_dump()) if template else None
