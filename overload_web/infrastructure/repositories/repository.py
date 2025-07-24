"""A class representing a relational database for `Template` objects.

Classes:

`SqlModelRepository`
    `SQLAlchemy` implementation of `SqlRepositoryProtocol` for managing
    `Template` objects in a SQL database.
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence, Union

from sqlmodel import Session, select

from overload_web.domain import protocols
from overload_web.infrastructure.repositories import tables

logger = logging.getLogger(__name__)


class SqlModelRepository(protocols.repositories.SqlRepositoryProtocol[tables.Template]):
    """
    `SQLAlchemy` repository for `Template` objects.

    Args:
        session: a `SQLAlchemy` session.
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: Union[str, int]) -> Optional[tables.Template]:
        """
        Retrieve a `Template` object by its ID.

        Args:
            id: the primary key of the `Template`.

        Returns:
            a `Template` instance or `None` if not found.
        """
        return self.session.get(tables.Template, id)

    def list(
        self, offset: Optional[int] = 0, limit: Optional[int] = 0
    ) -> Sequence[tables.Template]:
        """
        Retrieve all `Template` objects in the database.

        Args:
            offset: start position of `Template` objects to return
            limit: the maximum number of `Template` objects to return

        Returns:
            a sequence of `Template` objects.
        """
        statement = select(tables.Template).offset(offset).limit(limit)
        results = self.session.exec(statement)
        return results.all()

    def save(self, obj: tables.Template) -> None:
        """
        Adds a new or updated `Template` to the database.

        Args:
            template: the `Template` object to save.
        """
        self.session.add(obj)
