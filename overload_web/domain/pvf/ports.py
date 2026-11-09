"""Protocols defining ports used in domain services."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Sequence
from types import TracebackType
from typing import Any, Protocol, Self, TypeVar, runtime_checkable

from overload_web.domain.shared import Command, Event

logger = logging.getLogger(__name__)

T = TypeVar("T")  # invariant `bookops_marc.Bib` and `SQLModel` types


@runtime_checkable
class BibFetcher(Protocol):  # pragma: no branch
    """Protocol for a service that searches Sierra for bibs based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    session: Any

    def get_bibs_by_id(self, value: str | int, key: str) -> Sequence[dict[str, Any]]:
        """Retrieve candidate bib records that match a key-value pair.

        Args:
            key: The field name corresponding to the identifier (eg. "isbn").
            value: The identifier value to search by (eg. "9781234567890").

        Returns:
            a list of dictionaries representing candidate matches.

        """
        ...


@runtime_checkable
class FileRetriever(Protocol):  # pragma: no branch
    """A protocol for a service which retrieves files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def download(self, dir: str, name: str) -> bytes:
        """Download the content of a specific file.

        Args:
            dir: the directory where the file is located
            name: the name of the file to load

        Returns:
            the content of the specified file as a `bytes` object

        """
        ...

    def list(self, dir: str) -> list[str]:
        """List available files.

        Args:
            dir: the directory whose files to list

        Returns:
            a list of file names as strings

        """
        ...


@runtime_checkable
class FileStorage(Protocol[T]):  # pragma: no branch
    """A protocol for a service which allows for file IO operations.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def load(self, reference: str) -> bytes:
        """Load a file.

        Args:
            reference: the path to the file

        Returns:
            the content of the specified file as a `bytes` object

        """
        ...

    def save(self, id: str, filename: str, content: bytes) -> str:
        """Save a file to a location on storage.

        Args:
            content: the content of the file as a bytes object.
            filename: the name of the file.
            id: the workflow_id for the file.

        Returns:
            the path where the file was saved as a string

        """
        ...

    def save_intermediate_records(self, id: str, job: T) -> None:
        """Save records at intermediate stage of processing workflow."""
        ...

    def load_intermediate_records(self, id: str) -> T:
        """Load records from intermediate stage of processing workflow."""
        ...


@runtime_checkable
class FileWriter(Protocol):  # pragma: no branch
    """A protocol for a service for use within Overload which writes files.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def write(self, dir: str, file: bytes, file_name: str) -> str:
        """Write content to a specific file.

        Args:
            dir: the directory where the file should be written
            file: the file content to write as a `bytes` object
            file_name: the name of the file to be writen

        Returns:
            the name of the file that has just been written

        """
        ...


@runtime_checkable
class MarcParserPort(Protocol[T]):  # pragma: no branch
    """Protocol for a class which parses MARC records."""

    def compare_mapped_tags(self, obj: T, tags: dict[str, dict[str, str]]) -> bool:
        """Match vendor tags from mapping to bib object."""
        ...

    def create_bib_obj(self, data: bytes, library: str) -> T:
        """Instantiate a Bib object from binary data."""
        ...

    def get_reader(self, data: bytes, library: str) -> Iterator:
        """Instantiate an object that can read MARC binary as an iterator."""
        ...

    def identify_vendor(self, obj: T, mapping: dict[str, Any]) -> dict[str, Any]:
        """Determine the vendor who created a `bookops_marc.Bib` record."""
        ...

    def map_bib_data(self, obj: T, mapping: dict[str, Any]) -> dict[str, Any]:
        """Map an bib to a dictionary following a set of rules."""
        ...

    def map_order_data(self, obj: T, mapping: dict[str, Any]) -> dict[str, Any]:
        """Map an order to a dictionary following a set of rules."""
        ...


@runtime_checkable
class MarcUpdaterPort(Protocol[T]):  # pragma: no branch
    """Protocol for a class which updates MARC records."""

    def create_bib(self, binary_data: bytes, library: str) -> T:
        """Create a `bookops_marc.Bib` object from a `bytes` object."""
        ...

    def update_fields(self, bib: T, field_updates: list[Any]) -> None:
        """Update record in place."""
        ...

    def update_leader_encoding(self, bib: T, leader: str) -> None:
        """Update character encoding to unicode."""
        ...


@runtime_checkable
class MessageBusPort(Protocol):  # pragma: no branch
    """Protocol for a class which can publish events and call send commands."""

    def register_command(self, command_type: type[Command], handler: Callable) -> None:
        """Register a handler for a command."""
        ...

    def register_event(self, command_type: type[Event], handler: Callable) -> None:
        """Register a listener for an event."""
        ...

    def send(self, command: Command) -> None:
        """Route a command to its handler."""
        ...

    def publish(self, event: Event) -> None:
        """Publish and event to all listeners."""
        ...


@runtime_checkable
class ReportWriter(Protocol):  # pragma: no branch
    """A protocol defining a service used to write report data."""

    def prep_report(self, data: list[dict[str, Any]]) -> list[list[Any]]:
        """Prep data to write to an external service."""
        ...

    def write_report(self, data: list[list[Any]]) -> None:
        """Write report data to an external service."""
        ...


@runtime_checkable
class TemplateRepositoryProtocol(Protocol[T]):  # pragma: no branch
    """Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    def get(self, id: str) -> T | None:
        """Get objects from a database."""
        ...

    def list(self, offset: int | None = 0, limit: int | None = 0) -> Sequence[T]:
        """List all objects in a database."""
        ...

    def save(self, obj: T) -> T:
        """Save a new object to a database."""
        ...

    def update(self, data: T, id: str) -> T | None:
        """Update an existing object in a database."""
        ...


@runtime_checkable
class BatchRepositoryProtocol(Protocol[T]):  # pragma: no branch
    """Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    def get(self, id: str) -> T | None:
        """Get objects from a database."""
        ...

    def save(self, obj: T) -> T:
        """Save a new object to a database."""
        ...


@runtime_checkable
class IncomingFileRepositoryProtocol(Protocol[T]):  # pragma: no branch
    """Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    def delete(self, id: str) -> None:
        """Delete an object from a database."""
        ...

    def list_by_id(self, id: str | int) -> Sequence[T]:
        """List all objects in a database filtering by a specific id."""
        ...

    def save(self, obj: T) -> T:
        """Save a new object to a database."""
        ...


@runtime_checkable
class WorkflowRepositoryProtocol(Protocol[T]):  # pragma: no branch
    """Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    def get(self, id: str) -> T | None:
        """Get objects from a database."""
        ...

    def update(self, data: T, id: str) -> T | None:
        """Update an existing object in a database."""
        ...

    def save(self, obj: T) -> T:
        """Save a new object to a database."""
        ...


@runtime_checkable
class UnitOfWorkProtocol(Protocol):  # pragma: no branch
    """Protocol defining the Unit of Work for database transactions."""

    incoming_files: IncomingFileRepositoryProtocol
    order_templates: TemplateRepositoryProtocol
    processed_batches: BatchRepositoryProtocol
    workflow_states: WorkflowRepositoryProtocol

    def __enter__(self) -> Self:
        """Open a UnitOfWork object as a context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the context manager."""
        ...

    def commit(self) -> None:
        """Commit all changes to a database."""
        ...

    def rollback(self) -> None:
        """Rollback changes and do not commit them to the database."""
        ...
