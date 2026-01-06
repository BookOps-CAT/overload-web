"""Protocols for defining services that retrieve and parse bib records.

This module defines the fetcher used in the infrastructure layer responsible for
finding the duplicate records in Sierra for a `DomainBib` as well as the parser,
vendor identifier, and updater used in the infrastructure layer to convert data
between pymarc/bookops_marc objects and domain objects. Concrete implementations of
these protocols are defined in the infrastructure layer.

Protocols:

`BibFetcher`
    a protocol that defines the any adapter to Sierra that is capable of retrieving
    records based on identifier keys. Matching is based on specific identifiers such
    as OCLC number, ISBN, or Sierra Bib ID.

`BibMapper`
    a protocol that defines an adapter used to convert MARC objects to domain
    objects.

`BibUpdater`
    a protocol that defines an adapter used to update MARC records based on attributes
    of domain objects and rules.
"""

from __future__ import annotations

import logging
from typing import Any, BinaryIO, Iterator, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

C = TypeVar("C", contravariant=True)  # variable for contravariant DomainBib type
D = TypeVar("D")  # variable for invariant DomainBib type
F = TypeVar("F")  # variable for BaseSierraResponse type


@runtime_checkable
class BibFetcher(Protocol[F]):
    """
    Protocol for a service that can fetch bib records from Sierra based on an
    identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[F]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """


@runtime_checkable
class BibMapper(Protocol[C]):
    """Map object to `DomainBib` based on rules"""

    rules: dict[str, Any]

    def get_reader(self, data: bytes | BinaryIO) -> Iterator: ...  # pragma: no branch

    def identify_vendor(self, record: C) -> dict[str, Any]: ...  # pragma: no branch

    def map_data(self, record: C) -> dict[str, Any]: ...  # pragma: no branch


@runtime_checkable
class BibUpdater(Protocol[D]):
    """
    Update MARC records with appropriate fields during last stage of record processing.
    """

    rules: dict[str, dict[str, str]]

    def update_acquisitions_record(
        self, record: D, template_data: dict[str, Any]
    ) -> D: ...  # pragma: no branch

    def update_cataloging_record(self, record: D) -> D: ...  # pragma: no branch

    def update_selection_record(
        self, record: D, template_data: dict[str, Any]
    ) -> D: ...  # pragma: no branch


@runtime_checkable
class ResultsReviewer(Protocol[C, F]):
    """Review results of Sierra queries and select best match"""

    def review_results(
        self, input: C, results: list[F]
    ) -> str | None: ...  # pragma: no branch
