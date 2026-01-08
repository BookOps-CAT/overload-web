"""Protocols for defining services that retrieve and parse bib records.

This module defines the fetcher used in the infrastructure layer responsible for
finding the duplicate records in Sierra for a `DomainBib` as well as the parser,
vendor identifier, and updater used in the infrastructure layer to convert data
between pymarc/bookops_marc objects and domain objects. Concrete implementations of
these protocols are defined in the infrastructure layer.

Protocols:

`BibFetcher`
    A protocol that defines the any adapter to Sierra that is capable of retrieving
    records based on identifier keys. Matching is based on specific identifiers such
    as OCLC number, ISBN, or Sierra Bib ID.

`BibMapper`
    A protocol that defines an adapter used to convert MARC objects to domain
    objects.

`BibMatchAnalyzer`
    A protocol that defines

`MarcUpdateHandler`
    A protocol that defines

`BibUpdater`
    A protocol that defines an adapter used to update MARC records based on attributes
    of domain objects and rules.
"""

from __future__ import annotations

import logging
from typing import Any, BinaryIO, Iterator, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # variable for contravariant `DomainBib` type
U = TypeVar("U")  # variable for invariant `BaseSierraResponse` type
V = TypeVar("V")  # variable for invariant `MatchResolution` type


@runtime_checkable
class BibFetcher(Protocol[U]):
    """
    Protocol for a service that can fetch bib records from Sierra based on an
    identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[U]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: The identifier value to search by (eg. "9781234567890").
        key: The field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of `BaseSierraResponse` objects representing candidate matches.
    """


@runtime_checkable
class BibMapper(Protocol[T]):
    """
    Protocol for a service that can map domain objects representing bib records
    to MARC based on a set of rules.

    This abstraction allows the `BibParser` to remain decoupled from any tool
    or library that may be used to read MARC data. Implementations may include
    `pymarc`, `bookops_marc` or other tools.
    """

    rules: dict[str, Any]

    def get_reader(self, data: bytes | BinaryIO) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def identify_vendor(self, record: T) -> dict[str, Any]: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def map_data(self, record: T) -> dict[str, Any]: ...  # pragma: no branch

    """Map MARC record to a domain object representing the record."""


# @runtime_checkable
# class BibMatchAnalyzer(Protocol[T, U, V]):
#     """Review results of Sierra queries and select best match"""

#     def resolve(self, incoming: T, candidates: list[U]) -> V: ...  # pragma: no branch


@runtime_checkable
class MarcUpdateHandler(Protocol[T]):
    full_record_pipelines: dict[str, Any]
    order_pipelines: dict[str, Any]
    library_pipelines: dict[str, Any]

    def create_order_marc_ctx(
        self, record: T, rules: dict[str, Any], template_data: dict[str, Any]
    ) -> Any: ...  # pragma: no branch

    def create_library_ctx(
        self, bib_id: str | None, bib_rec: T, vendor: str | None
    ) -> Any: ...  # pragma: no branch

    def create_full_marc_ctx(self, record: T) -> Any: ...  # pragma: no branch


class MatchAnalyzer(Protocol[U]):
    def review_candidates(self, candidates: list[U]) -> tuple: ...  # pragma: no branch
