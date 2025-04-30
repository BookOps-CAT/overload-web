"""
Classes representing a relational database for `Template` objects.

Protocols:

`RepositoryProtocol`
    Defines expected methods for a template repository.

Classes:

`SqlAlchemyRepository`
    `SQLAlchemy` implementation for managing `Template` objects in a database.
"""

from __future__ import annotations

from typing import Protocol, Union, runtime_checkable

from overload_web.domain import model


@runtime_checkable
class RepositoryProtocol(Protocol):
    """
    Interface for repository operations on `Template` objects.

    Includes methods for fetching and saving templates.
    """

    def get(self, id: Union[str, int]) -> model.Template: ...

    def save(self, template: model.Template) -> None: ...


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
        return self.session.query(model.Template).filter_by(id=id).first()

    def save(self, template: model.Template) -> None:
        """
        Adds a new or updated `Template` to the database.

        Args:
            template: the `Template` object to save.
        """
        self.session.add(template)
