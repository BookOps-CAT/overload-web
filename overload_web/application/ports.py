"""Protocols defining ports used in application services."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Protocol, Sequence, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # variable for contravariant `SQLModel` type
U = TypeVar("U")  # variable for invariant `SQLModel` type
V = TypeVar("V", contravariant=True)  # variable for contravariant `DomainBib` type
W = TypeVar("W")  # variable for invariant `bookops_marc.Bib` type


@runtime_checkable
class FileRetriever(Protocol):
    """
    A protocol for a service which retrieves files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def list(self, dir: str) -> list[str]: ...  # pragma: no branch

    """
    List available files.

    Args:
        dir: the directory whose files to list

    Returns:
        a list of file names as strings
    """

    def download(self, name: str, dir: str) -> bytes: ...  # pragma: no branch

    """
    Download the content of a specific file.

    Args:
        name: the name of the file to load
        dir: the directory where the file is located

    Returns:
        the content of the specified file as a `bytes` object
    """


@runtime_checkable
class FileStorage(Protocol):
    """
    A protocol for a service which saves files to storage and loads them for processing
    within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def load(self, reference: str) -> bytes: ...  # pragma: no branch

    """
    Load a file.

    Args:
        reference: the path to the file

    Returns:
        the content of the specified file as a `bytes` object
    """

    def save(
        self, id: str, filename: str, content: bytes
    ) -> str: ...  # pragma: no branch

    """
    Save a file to a location on storage.

    Args:
        id: the workflow_id for the file.
        filename: the name of the file.
        content: the content of the file as a bytes object.

    Returns:
        the path where the file was saved as a string
    """


@runtime_checkable
class FileWriter(Protocol):
    """
    A protocol for a service for use within Overload which writes files.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def write(
        self, file: bytes, file_name: str, dir: str
    ) -> str: ...  # pragma: no branch

    """
    Write content to a specific file.

    Args:
        file: the file content to write as a `bytes` object
        file_name: the name of the file to be writen
        dir: the directory where the file should be written

    Returns:
        the name of the file that has just been written
    """


@runtime_checkable
class ReportWriter(Protocol):
    """A protocol defining a service used to write report data."""

    def prep_report(
        self, data: list[dict[str, Any]]
    ) -> list[list[Any]]: ...  # pragma: no branch

    """Prep data to write to an external service."""

    def write_report(self, data: list[list[Any]]) -> None: ...  # pragma: no branch

    """Write report data to an external service."""


@runtime_checkable
class SqlRepositoryProtocol(Protocol[T]):
    """
    Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    session: Any

    def delete(self, id: str) -> None: ...  # pragma: no branch

    """Delete an object from a database."""

    def get(self, id: str) -> dict[str, Any] | None: ...  # pragma: no branch

    """Get objects from a database."""

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[dict[str, Any]]: ...  # pragma: no branch

    """List all objects in a database."""

    def list_by_id(
        self, id: str | int
    ) -> Sequence[dict[str, Any]]: ...  # pragma: no branch

    """List all objects in a database filtering by a specific id."""

    def save(self, obj: T) -> dict[str, Any]: ...  # pragma: no branch

    """Save a new object to a database."""

    def update(
        self, id: str, data: T
    ) -> dict[str, Any] | None: ...  # pragma: no branch

    """Update an existing object in a database."""


class UnitOfWorkProtocol(Protocol):
    """Protocol defining the Unit of Work for database transactions."""

    incoming_files: SqlRepositoryProtocol
    order_templates: SqlRepositoryProtocol
    processed_batches: SqlRepositoryProtocol

    def __enter__(self) -> UnitOfWorkProtocol: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
