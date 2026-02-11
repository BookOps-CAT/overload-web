"""Port used to define a database for order templates.

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.

"""

from __future__ import annotations

import logging
from typing import (
    Any,
    BinaryIO,
    Iterator,
    Protocol,
    Sequence,
    TypeVar,
    runtime_checkable,
)

from overload_web.domain.models import bibs, files, sierra_responses

logger = logging.getLogger(__name__)

T = TypeVar("T")


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that searches Sierra for bib records based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[sierra_responses.BaseSierraResponse]: ...  # pragma: no branch

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

    def load(self, name: str, dir: str) -> files.VendorFile: ...  # pragma: no branch

    """
    Load the content of a specific file.

    Args:
        name: the name of the file to load
        dir: the directory where the file is located

    Returns:
        the specified file as a `VendorFile` object
    """


@runtime_checkable
class FileWriter(Protocol):
    """
    A protocol for a service which writes .mrc files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def write(self, file: files.VendorFile, dir: str) -> str: ...  # pragma: no branch

    """
    Write a content to a specific file.

    Args:
        file: the file to write as a `VendorFile` object
        dir: the directory where the file should be written

    Returns:
        the name of the file that has just been written
    """


@runtime_checkable
class MarcEnginePort(Protocol[T]):
    bib_rules: dict[str, Any]
    library: str
    order_rules: dict[str, Any]
    record_type: str
    collection: str | None
    vendor_rules: dict[str, Any]
    _config: Any

    def create_bib_from_domain(
        self, record: bibs.DomainBib
    ) -> T: ...  # pragma:no branch

    """Create a `bookops_marc.Bib` object from a `DomainBib` object"""

    def get_command_tag_field(self, bib: T) -> Any | None: ...  # pragma: no branch

    """Get the Sierra command tag from a bib record if present."""

    def get_reader(self, data: bytes | BinaryIO) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def get_value_of_field(
        self, tag: str, bib: T
    ) -> str | None: ...  # pragma: no branch

    """Get the value of a MARC field by it's tag. Retrieves first field."""

    def get_vendor_tags_from_bib(
        self, record: T, tags: dict[str, dict[str, str]]
    ) -> bool: ...  # pragma:no branch

    def identify_vendor(
        self, record: T, rules: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Determine the vendor who created a `bookops_marc.Bib` record."""

    def map_data(
        self, obj: Any, rules: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Map an object to a dictionary following a set of rules."""

    def update_fields(
        self, field_updates: list[Any], bib: T
    ) -> None: ...  # pragma:no branch

    """Update record in place"""


@runtime_checkable
class SqlRepositoryProtocol(Protocol[T]):
    """
    Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    session: Any

    def get(self, id: str) -> T | None: ...  # pragma: no branch

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[T]: ...  # pragma: no branch

    def save(self, obj: T) -> T: ...  # pragma: no branch

    def update_template(self, id: str, data: T) -> T | None: ...  # pragma: no branch


class ReportHandler(Protocol):
    @staticmethod
    def create_vendor_breakdown(
        report_data: dict[str, list[Any]],
    ) -> dict[str, list[Any]]: ...  # pragma: no branch

    @staticmethod
    def create_duplicate_report(
        report_data: dict[str, list[Any]],
    ) -> list[list[Any]]: ...  # pragma: no branch

    @staticmethod
    def create_call_number_report(
        report_data: dict[str, Any],
    ) -> list[list[Any]]: ...  # pragma: no branch

    @staticmethod
    def list2dict(
        report_data: list[bibs.MatchAnalysis],
    ) -> dict[str, list[Any]]: ...  # pragma: no branch

    @staticmethod
    def report_to_html(
        report_data: dict[str, list[Any]], classes: list[str]
    ) -> str: ...  # pragma: no branch
