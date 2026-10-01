"""Protocols defining ports used in domain services."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Iterator, Protocol, Sequence, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # contravariant `DomainBib` and `SQLModel` types
U = TypeVar("U")  # invariant `bookops_marc.Bib` and `SQLModel` types


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that searches Sierra for bib records based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    session: Any

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> Sequence[dict[str, Any]]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value pair.

    Args:
        key: The field name corresponding to the identifier (eg. "isbn").
        value: The identifier value to search by (eg. "9781234567890").

    Returns:
        a list of dictionaries representing candidate matches.
    """


@runtime_checkable
class FileRetriever(Protocol):
    """
    A protocol for a service which retrieves files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def download(self, dir: str, name: str) -> bytes: ...  # pragma: no branch

    """
    Download the content of a specific file.

    Args:
        dir: the directory where the file is located
        name: the name of the file to load

    Returns:
        the content of the specified file as a `bytes` object
    """

    def list(self, dir: str) -> list[str]: ...  # pragma: no branch

    """
    List available files.

    Args:
        dir: the directory whose files to list

    Returns:
        a list of file names as strings
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
        content: the content of the file as a bytes object.
        filename: the name of the file.
        id: the workflow_id for the file.
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
        self, dir: str, file: bytes, file_name: str
    ) -> str: ...  # pragma: no branch

    """
    Write content to a specific file.

    Args:
        dir: the directory where the file should be written
        file: the file content to write as a `bytes` object
        file_name: the name of the file to be writen

    Returns:
        the name of the file that has just been written
    """


@runtime_checkable
class MarcParserPort(Protocol[U, T]):
    def compare_mapped_tags(
        self, obj: U, tags: dict[str, dict[str, str]]
    ) -> bool: ...  # pragma:no branch

    """Match vendor tags from mapping to bib object."""

    def create_bib_obj(self, data: bytes, library: str) -> U: ...  # pragma: no branch

    """Instantiate a Bib object from binary data."""

    def get_reader(
        self, data: bytes, library: str
    ) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def identify_vendor(
        self, obj: U, mapping: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Determine the vendor who created a `bookops_marc.Bib` record."""

    def map_bib_data(
        self, obj: U, mapping: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Map an bib to a dictionary following a set of rules."""

    def map_order_data(
        self, obj: U, mapping: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Map an order to a dictionary following a set of rules."""

    def write(self, records: Sequence[T]) -> bytes: ...  # pragma:no branch

    """Write `DomainBib` objects to single binary object."""


@runtime_checkable
class MarcUpdaterPort(Protocol[T, U]):
    def create_bib_from_domain(self, record: T) -> U: ...  # pragma:no branch

    """Create a `bookops_marc.Bib` object from a `DomainBib` object"""

    def update_fields(
        self, bib: U, field_updates: list[Any]
    ) -> None: ...  # pragma:no branch

    """Update record in place"""

    def update_leader_encoding(
        self, bib: U, leader: str
    ) -> None: ...  # pragma:no branch

    """Update character encoding to unicode."""


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
        self, data: T, id: str
    ) -> dict[str, Any] | None: ...  # pragma: no branch

    """Update an existing object in a database."""


@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    """Protocol defining the Unit of Work for database transactions."""

    incoming_files: SqlRepositoryProtocol
    order_templates: SqlRepositoryProtocol
    processed_batches: SqlRepositoryProtocol

    def __enter__(self) -> UnitOfWorkProtocol: ...  # pragma: no branch

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...  # pragma: no branch

    def commit(self) -> None: ...  # pragma: no branch
    def rollback(self) -> None: ...  # pragma: no branch
