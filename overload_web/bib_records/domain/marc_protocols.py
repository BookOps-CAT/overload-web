"""Protocols for defining services that retrieve and parse bib records.

This module defines the fetcher used in the infrastructure layer responsible for
finding the duplicate records in Sierra for a `DomainBib` as well as the parser
used in the infrastructure layer to convert data between pymarc/bookops_marc objects
and domain objects.

Protocols:

`BibFetcher`
    a protocol that defines the any adapter to Sierra that is capable of retrieving
    records based on identifier keys. Matching is based on specific identifiers such
    as OCLC number, ISBN, or Sierra Bib ID. Concrete implementations of this protocol
    are defined in the infrastructure layer.

`MarcParser`
    a protocol that defines an adapter used to convert MARC objects to domain
    objects. Concrete implementations of this protocol are defined in the infrastructure
    layer.

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, BinaryIO, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.bib_records.domain import responses

T = TypeVar("T")

logger = logging.getLogger(__name__)


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that can fetch bib records from Sierra based on an
    identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[responses.FetcherResponseDict]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """


@runtime_checkable
class MarcParser(Protocol[T]):
    """
    Parse binary MARC data to a generic type, `T`.

    Args:
        rules: the marc mapping rules to be used when processing records
        library: the library whose records are being parsed
    """

    rules: dict[str, dict[str, str | dict[str, str]]]
    library: str

    def parse(self, data: BinaryIO | bytes) -> list[T]: ...  # pragma: no branch

    """Convert binary MARC data into a list of `T` objects."""

    def serialize(self, records: list[T]) -> BinaryIO: ...  # pragma: no branch

    """Convert a list of `T` objects into binary MARC data."""


@runtime_checkable
class MarcUpdater(Protocol[T]):
    """
    Update MARC records with appropriate fields during last stage of record processing.
    """

    rules: dict[str, dict[str, str]]

    def update_bib_data(self, bib: T) -> T: ...  # pragma: no branch

    """Update MARC fields in a full-level `T` object based on rules."""

    def update_order(self, bib: T) -> T: ...  # pragma: no branch

    """Update MARC fields in an order-level `T` object based on rules."""

    def update_record(
        self, bib: T, template_data: dict[str, Any]
    ) -> T: ...  # pragma: no branch

    """Update a MARC record `T` object."""
