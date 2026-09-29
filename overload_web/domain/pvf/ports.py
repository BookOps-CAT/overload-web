"""Protocols defining ports used in domain services."""

from __future__ import annotations

import logging
from typing import Any, Iterator, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # variable for contravariant `DomainBib` type
U = TypeVar("U")  # variable for invariant `bookops_marc.Bib` type


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
class MarcParserPort(Protocol[U]):
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

    def write(self, records: list[T]) -> bytes: ...  # pragma:no branch

    """Write `DomainBib` objects to single binary object."""


@runtime_checkable
class MarcUpdaterPort(Protocol[T, U]):
    library: str
    record_type: str
    collection: str | None
    config: dict[str, Any]

    def create_bib_from_domain(self, record: T) -> U: ...  # pragma:no branch

    """Create a `bookops_marc.Bib` object from a `DomainBib` object"""

    def update_fields(
        self, field_updates: list[Any], bib: U
    ) -> None: ...  # pragma:no branch

    """Update record in place"""

    def update_leader_encoding(
        self, leader: str, bib: U
    ) -> None: ...  # pragma:no branch

    """Update character encoding to unicode."""
