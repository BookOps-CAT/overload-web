"""Protocols for defining services that interact with Sierra.

This module defines the fetcher used in the infrastructure layer responsible for
finding the duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.

Protocols:

`BibFetcher`
    a protocol that defines the contract for any adapter to Sierra that
    is capable of retrieving records based on identifier keys. Concrete
    implementations of this protocol are defined in the infrastructure layer.

"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that can fetch bib records from Sierra based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations may a REST APIs, BPL's Solr service, NYPL's
    Platform serivce, or other systems.
    """

    def get_bibs_by_id(self, value: str | int, key: str) -> list[dict[str, Any]]: ...

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """
