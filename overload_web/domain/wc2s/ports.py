"""Protocols defining ports used in domain services."""

from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T", covariant=True)  # variable for covariant `bookops_marc.Bib` type


@runtime_checkable
class MarcParserPort(Protocol[T]):  # pragma: no branch
    """Parse a MARC record using external libraries."""

    def create_bib_obj(self, data: bytes, library: str) -> T:
        """Instantiate a Bib object from binary data."""
        ...


@runtime_checkable
class OCLCBibFetcher(Protocol):  # pragma: no branch
    """Interface for interactions with OCLC Metadata/Search APIs."""

    def get_brief_bibs_by_id(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Search for brief bib resource using specified parameters."""
        ...

    def get_full_bib_by_id(self, oclc_number: str) -> bytes:
        """Retrieve for full MARC record as a bytes object for a given ID."""
        ...

    def get_full_bib_json_by_id(self, oclc_number: str) -> dict[str, Any]:
        """Retrieve for full MARC record as a json object for a given ID."""
        ...
