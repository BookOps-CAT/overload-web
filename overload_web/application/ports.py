"""Protocols defining ports used in application services."""

from __future__ import annotations

import logging
from typing import Any, Iterator, Protocol, Sequence, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

R = TypeVar("R")  # variabe for `ProcessingStatistics` report type
S = TypeVar("S")  # variable for `BaseSierraResponse` type
T = TypeVar("T", contravariant=True)  # variable for `OrderTemplate` type
U = TypeVar("U", contravariant=True)  # variable for `DomainBib` contravariant type
V = TypeVar("V")  # variable for `DomainBib` type


@runtime_checkable
class BibFetcher(Protocol[S]):
    """
    Protocol for a service that searches Sierra for bib records based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    session: Any

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[S]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value pair.

    Args:
        value: The identifier value to search by (eg. "9781234567890").
        key: The field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of `BaseSierraResponse` objects representing candidate matches.
    """


@runtime_checkable
class FileLoader(Protocol):
    """
    A protocol for a service which loads .mrc files for use within Overload.

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

    def load(self, name: str, dir: str) -> bytes: ...  # pragma: no branch

    """
    Load the content of a specific file.

    Args:
        name: the name of the file to load
        dir: the directory where the file is located

    Returns:
        the content of the specified file as a `bytes` object
    """


@runtime_checkable
class FileWriter(Protocol):
    """
    A protocol for a service for use within Overload which writes .mrc files.

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
class MarcEnginePort(Protocol[U, V]):
    bib_rules: dict[str, Any]
    library: str
    order_rules: dict[str, Any]
    record_type: str
    collection: str | None
    vendor_rules: dict[str, Any]
    default_loc: str
    bib_id_tag: str
    marc_order_mapping: dict[str, Any]
    config: Any

    def create_bib_from_domain(self, record: U) -> V: ...  # pragma:no branch

    """Create a `bookops_marc.Bib` object from a `DomainBib` object"""

    def get_command_tag_field(self, bib: V) -> Any | None: ...  # pragma: no branch

    """Get the Sierra command tag from a bib record if present."""

    def get_reader(self, data: bytes) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def get_vendor_tags_from_bib(
        self, record: V, tags: dict[str, dict[str, str]]
    ) -> bool: ...  # pragma:no branch

    def identify_vendor(
        self, record: V, rules: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Determine the vendor who created a `bookops_marc.Bib` record."""

    def map_data(
        self, obj: Any, rules: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Map an object to a dictionary following a set of rules."""

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

    def get(self, id: str) -> dict[str, Any] | None: ...  # pragma: no branch

    """Get objects from a database."""

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[dict[str, Any]]: ...  # pragma: no branch

    """List objects in a database."""

    def save(self, obj: T) -> dict[str, Any]: ...  # pragma: no branch

    """Save a new object to a database."""

    def update(
        self, id: str, data: T
    ) -> dict[str, Any] | None: ...  # pragma: no branch

    """Update an existing object in a database."""


class ReportHandler(Protocol):
    """A protocol defining a service used to create processing reports."""

    library: str
    collection: str | None
    record_type: str

    def create_call_number_report(
        self, report_data: R, record_type: str
    ) -> dict[str, list[Any]]: ...  # pragma: no branch

    def create_detailed_report(
        self, report_data: R
    ) -> dict[str, list[Any]]: ...  # pragma: no branch

    def create_duplicate_report(
        self, report_data: R
    ) -> dict[str, list[Any]]: ...  # pragma: no branch

    def create_vendor_report(
        self, report_data: R
    ) -> dict[str, list[Any]]: ...  # pragma: no branch


class ReportWriter(Protocol):
    """A protocol defining a service used to write report data."""

    def prep_report(
        self, data: dict[str, list[Any]]
    ) -> list[list[Any]]: ...  # pragma: no branch

    """Prep data to write to an external service."""

    def write_report(self, data: list[list[Any]]) -> None: ...  # pragma: no branch

    """Write report data to an external service."""
