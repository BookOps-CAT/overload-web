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

import logging
from typing import Optional, Protocol, TypeVar, Union, runtime_checkable

from overload_web.domain import model

logger = logging.getLogger(__name__)


T = TypeVar("T")
K = TypeVar("K", contravariant=True)


@runtime_checkable
class RepositoryProtocol(Protocol[T, K]):
    """
    Interface for repository operations on different object types.

    Includes methods for fetching and saving objects.
    """

    def delete(self, obj: T) -> None: ...

    """Delete and object from the database."""

    def get(self, id: K) -> Optional[T]: ...

    """Retrieve an object by its ID."""

    def list(self) -> list[T]: ...

    """List all objects of the type in the database."""

    def save(self, obj: T) -> None: ...

    """Save a new or updated object to the database."""


class SqlAlchemyTemplateRepository:
    """
    `SQLAlchemy` repository for `Template` objects.
    Args:
        session: a `SQLAlchemy` session.
    """

    def __init__(self, session):
        self.session = session

    def delete(self, obj: model.Template) -> None:
        """
        Deletes a `Template` object from the database.

        Args:
            template: the `Template` object to delete.
        """
        self.session.delete(obj)

    def get(self, id: Union[str, int]) -> Optional[model.Template]:
        """
        Retrieve a `Template` object by its ID.

        Args:
            id: the primary key of the `Template`.

        Returns:
            a `Template` instance or `None` if not found.
        """
        return self.session.query(model.Template).filter_by(id=id).first()

    def list(self) -> list[model.Template]:
        """
        List all `Template` objects in the database.

        Returns:
            a list of `Template` instances.
        """
        return self.session.query(model.Template).all()

    def save(self, obj: model.Template) -> None:
        """
        Adds a new or updated `Template` to the database.

        Args:
            template: the `Template` object to save.
        """
        self.session.add(obj)


class SqlAlchemyVendorFileRepository:
    """
    `SQLAlchemy` repository for `VendorFile` objects.

    Args:
        session: a `SQLAlchemy` session.
    """

    def __init__(self, session):
        self.session = session

    def delete(self, obj: model.VendorFile) -> None:
        """
        Deletes a `VendorFile` object from the database.

        Args:
            file: the `VendorFile` object to delete.
        """
        self.session.delete(obj)

    def get(self, id: Union[str, int]) -> Optional[model.VendorFile]:
        """
        Retrieve a `VendorFile` object by its ID.

        Args:
            id: the primary key of the `VendorFile`.

        Returns:
            a `VendorFile` instance or `None` if not found.
        """
        return self.session.query(model.VendorFile).filter_by(id=id).first()

    def list(self) -> list[model.VendorFile]:
        """
        List all `VendorFile` objects in the database.

        Returns:
            a list of `VendorFile` instances.
        """
        return self.session.query(model.VendorFile).all()

    def save(self, file: model.VendorFile) -> None:
        """
        Adds a new or updated `VendorFile` to the database.

        Args:
            VendorFile: the `VendorFile` object to save.
        """
        self.session.add(file)
