"""A class representing a relational database for `OrderTemplate` objects.

Classes:

`SqlModelRepository`
    `SQLModel` implementation of `SqlRepositoryProtocol` for managing
    `OrderTemplate` objects in a SQL database.
"""

from __future__ import annotations

import logging
from typing import Sequence

from sqlmodel import Session, select

from overload_web.domain import protocols
from overload_web.infrastructure.db import tables

logger = logging.getLogger(__name__)


class SqlModelRepository(
    protocols.repositories.SqlRepositoryProtocol[tables.OrderTemplate]
):
    """
    `SQLModel` repository for `OrderTemplate` objects.

    Args:
        session: a `sqlmodel.Session`.
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str | int) -> tables.OrderTemplate | None:
        """
        Retrieve a `OrderTemplate` object by its ID.

        Args:
            id: the primary key of the `OrderTemplate`.

        Returns:
            a `OrderTemplate` instance or `None` if not found.
        """
        return self.session.get(tables.OrderTemplate, id)

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[tables.OrderTemplate]:
        """
        Retrieve all `OrderTemplate` objects in the database.

        Args:
            offset: start position of `OrderTemplate` objects to return
            limit: the maximum number of `OrderTemplate` objects to return

        Returns:
            a sequence of `OrderTemplate` objects.
        """
        statement = select(tables.OrderTemplate).offset(offset).limit(limit)
        results = self.session.exec(statement)
        return results.all()

    def save(self, obj: tables.OrderTemplate) -> None:
        """
        Adds a new `OrderTemplate` to the database.

        Args:
            obj: the `OrderTemplate` object to save.
        """
        self.session.add(obj)

    def update(self, id: str, data: dict[str, str]) -> tables.OrderTemplate | None:
        """
        Updates an existing `OrderTemplate` in the database.

        Args:
            id: the id of the template to be updated
            data: the data to be used to update the existing template.
        Returns:
            a `OrderTemplate` instance or `None` if not found.
        """
        template = self.session.get(tables.OrderTemplate, id)
        if not template:
            logger.error(f"Template '{id}' does not exist")
            return None
        else:
            template.sqlmodel_update(data)
            self.session.add(template)
            return template
