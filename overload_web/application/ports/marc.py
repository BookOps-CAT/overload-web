from __future__ import annotations

import logging
from typing import Any, BinaryIO, Iterator, Protocol, TypeVar, runtime_checkable

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)

T = TypeVar("T")  # variable bookops_marc `Bib` type
U = TypeVar("U", covariant=True)  # variable for pymarc `Field` type


@runtime_checkable
class MarcEnginePort(Protocol[T]):
    bib_rules: dict[str, Any]
    library: str
    order_rules: dict[str, Any]
    record_type: str
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

    """Get the value of the first MARC field for a tag."""

    def get_vendor_tags_from_bib(
        self, record: T, tags: dict[str, dict[str, str]]
    ) -> bool: ...  # pragma:no branch

    def identify_vendor(
        self, record: T, rules: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: nobranch

    """Determine the vendor who created a `bookops_marc.Bib` record."""

    def map_data(
        self, obj: Any, rules: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Map an object to a dictionary following a set of rules."""

    def update_fields(
        self, field_updates: list[Any], bib: T
    ) -> None: ...  # pragma:no branch

    """Update record in place"""
