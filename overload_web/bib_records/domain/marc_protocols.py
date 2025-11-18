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

`MarcMapper`
    a protocol that defines an adapter used to convert MARC objects to domain
    objects.

`MarcUpdater`
    a protocol that defines an adapter used to update MARC records based on attributes
    of domain objects and rules.

`VendorIdentifier`
    a protocol that defines an adapter used to identify the vendor to created a record
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, BinaryIO, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BibDTOProtocol(Protocol):
    """Defines attributes of a BibDTO object for use as a TypeVar"""

    bib: Any
    domain_bib: Any
    vendor_info: Any


ConBib = TypeVar("ConBib", contravariant=True)  # for bookops_marc.Bib objects as inputs
D = TypeVar("D", bound=BibDTOProtocol)  # for BibDTO objects
InvarBib = TypeVar("InvarBib")  # for bookops_marc.Bib objects as return types


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
    ) -> list[bibs.FetcherResponseDict]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """


@runtime_checkable
class BibMapper(Protocol[ConBib]):
    """Map object to `DomainBib` based on rules"""

    rules: dict[str, Any]

    def map_bib(
        self, record: ConBib, info: bibs.VendorInfo
    ) -> BibDTOProtocol: ...  # pragma: no branch


@runtime_checkable
class MarcReaderProtocol(Protocol[InvarBib]):
    library: str

    def read_records(
        self, data: bytes | BinaryIO
    ) -> list[InvarBib]: ...  # pragma: no branch


@runtime_checkable
class MarcUpdater(Protocol[D]):
    """
    Update MARC records with appropriate fields during last stage of record processing.
    """

    rules: dict[str, dict[str, str]]

    def update_record(
        self, record: D, record_type: str, template_data: dict[str, Any]
    ) -> D: ...  # pragma: no branch

    """Update a MARC record `T` object."""


@runtime_checkable
class ResultsReviewer(Protocol):
    """Review results of Sierra queries and select best match"""

    record_type: str

    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.FetcherResponseDict]
    ) -> str | None: ...  # pragma: no branch


@runtime_checkable
class VendorIdentifier(Protocol[ConBib]):
    """Identify vendor based on rules"""

    rules: dict[str, Any]

    def identify_vendor(
        self, record: ConBib
    ) -> bibs.VendorInfo: ...  # pragma: no branch
