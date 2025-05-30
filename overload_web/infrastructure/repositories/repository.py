"""A class representing a relational database for `Template` objects.

Classes:

`SqlAlchemyRepository`
    `SQLAlchemy` implementation of `RepositoryProtocol` for managing
    `Template` objects in a SQL database.
"""

from __future__ import annotations

import logging
from typing import Union

from overload_web.domain.models import templates

logger = logging.getLogger(__name__)


class SqlAlchemyRepository:
    """
    `SQLAlchemy` repository for `Template` objects.

    Args:
        session: a `SQLAlchemy` session.
    """

    def __init__(self, session):
        self.session = session

    def get(self, id: Union[str, int]):
        """
        Retrieve a `Template` object by its ID.

        Args:
            id: the primary key of the `Template`.

        Returns:
            a `Template` instance or `None` if not found.
        """
        return self.session.query(templates.Template).filter_by(id=id).first()

    def save(self, template: templates.Template) -> None:
        """
        Adds a new or updated `Template` to the database.

        Args:
            template: the `Template` object to save.
        """
        self.session.add(template)
