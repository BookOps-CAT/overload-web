"""Protocols for defining services that retrieve and parse bib records.

This module defines the fetcher used in the infrastructure layer responsible for
finding the duplicate records in Sierra for a `DomainBib` as well as the parser
and updater used in the infrastructure layer to convert data between
pymarc/bookops_marc objects and domain objects.

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

`MarUpdater`
    a protocol that defines an adapter used to update MARC records based on attributes
    of domain objects and rules. Concrete implementations of this protocol are defined
    in the infrastructure layer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, BinaryIO, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.bib_records.domain import bibs


logger = logging.getLogger(__name__)


class MapperVar(Protocol):
    bib: Any
    domain_bib: Any
    vendor_info: Any


B = TypeVar("B", contravariant=True)  # for bookops_marc.Bib objects
D = TypeVar("D", bound=MapperVar)  # for BibDTO object


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
    ) -> list[bibs.responses.FetcherResponseDict]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """


@runtime_checkable
class MarcParser(Protocol[D]):
    """
    Parse binary MARC data to a generic type, `T`.

    Args:
        rules: the marc mapping rules to be used when processing records
        library: the library whose records are being parsed
    """

    rules: dict[str, dict[str, str | dict[str, str]]]
    library: str

    def parse(self, data: BinaryIO | bytes) -> list[D]: ...  # pragma: no branch

    """Convert binary MARC data into a list of `D` objects."""

    def serialize(self, records: list[D]) -> BinaryIO: ...  # pragma: no branch

    """Convert a list of `D` objects into binary MARC data."""


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


class VendorInfoVar(Protocol):
    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str


@runtime_checkable
class VendorIdentifier(Protocol):
    """Identify vendor based on rules"""

    rules: dict[str, Any]

    def identify_vendor(
        self, record: B, library: str
    ) -> VendorInfoVar: ...  # pragma: no branch


@runtime_checkable
class BibMapper(Protocol[B]):
    """Map object to `DomainBib` based on rules"""

    rules: dict[str, Any]

    def map_bib(
        self, record: B, info: VendorInfoVar
    ) -> MapperVar: ...  # pragma: no branch


@runtime_checkable
class BibReader(Protocol):
    def read_records(
        self, data: BinaryIO | bytes, library: str
    ) -> list[B]: ...  # pragma: no branch
