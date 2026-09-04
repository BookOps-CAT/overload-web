"""Protocols defining ports used in application services."""

from __future__ import annotations

import logging
from typing import Any, Iterator, Protocol, Sequence, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # variable for `SQLModel` type
U = TypeVar("U", contravariant=True)  # variable for `DomainBib` contravariant type
V = TypeVar("V")  # variable for `DomainBib` type


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
    ) -> list[dict[str, Any]]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value pair.

    Args:
        value: The identifier value to search by (eg. "9781234567890").
        key: The field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of dictionaries representing candidate matches.
    """


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
class MarcParsingHandlerPort(Protocol):
    library: str
    record_type: str
    collection: str | None
    bib_mapping: str
    order_mapping: dict[str, Any]
    vendor_rules: dict[str, Any]

    def get_reader(self, data: bytes) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def match_vendor_tags_from_bib(
        self, record: V, tags: dict[str, dict[str, str]]
    ) -> bool: ...  # pragma:no branch

    def identify_vendor(self, record: V) -> dict[str, Any]: ...  # pragma: no branch

    """Determine the vendor who created a `bookops_marc.Bib` record."""

    def map_bib_data(self, obj: V) -> dict[str, Any]: ...  # pragma: no branch

    """Map an bib to a dictionary following a set of rules."""

    def map_order_data(self, obj: V) -> dict[str, Any]: ...  # pragma: no branch

    """Map an order to a dictionary following a set of rules."""

    def parse_fields(self, obj: V) -> list[dict[str, Any]]: ...  # pragma: no branch

    """Map all marc fields to a list of dictionarys."""

    def write(self, records: list[U]) -> bytes: ...  # pragma:no branch

    """Write `DomainBib` objects to single binary object."""


@runtime_checkable
class MarcUpdateHandlerPort(Protocol[U, V]):
    library: str
    record_type: str
    collection: str | None
    config: dict[str, Any]

    def create_bib_from_domain(self, record: U) -> V: ...  # pragma:no branch

    """Create a `bookops_marc.Bib` object from a `DomainBib` object"""

    def update_fields(
        self, field_updates: list[Any], bib: V
    ) -> None: ...  # pragma:no branch

    """Update record in place"""


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
class OCLCBibFetcher(Protocol):
    """Interface for interactions with OCLC Metadata/Search APIs."""

    def get_brief_bibs_by_id(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]: ...  # pragma: no branch

    """Search for brief bib resource using specified parameters."""

    def get_full_bibs_by_id(self, value: str | int) -> bytes: ...  # pragma: no branch

    """Retrieve for full MARC record as a bytes object for a given ID."""

    def get_full_bib_json_by_id(
        self, value: str
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Retrieve for full MARC record as a json object for a given ID."""
