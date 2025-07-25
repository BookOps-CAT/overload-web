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
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    Protocol,
    TypedDict,
    TypeVar,
    runtime_checkable,
)

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.domain import models

T = TypeVar("T")

logger = logging.getLogger(__name__)


class FetcherResponseDict(TypedDict):
    """Defines the dict returned by `BibFetcher.get_bibs_by_id` method"""

    library: str
    orders: list[str]
    bib_id: str | None
    isbn: str | None
    oclc_number: list[str] | None
    upc: str | None


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that can fetch bib records from Sierra based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[FetcherResponseDict]: ...  # pragma: no branch

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
        library: the library to whom the records belong as a `LibrarySystem` object
        marc_rules: the marc mapping to be used when processing records

    """

    library: models.bibs.LibrarySystem
    marc_rules: dict[str, dict[str, str]]

    def parse(self, data: BinaryIO | bytes) -> list[T]: ...  # pragma: no branch

    """Convert binary MARC data into a list of `T` objects."""

    def serialize(self, records: list[T]) -> BinaryIO: ...  # pragma: no branch

    """Convert a list of `T` objects into binary MARC data."""

    def update_fields(
        self, record: T, fields: list[dict[str, str]]
    ) -> T: ...  # pragma: no branch

    """Provided a list of fields as dicts, update MARC fields in a `T` object"""
