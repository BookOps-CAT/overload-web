"""Domain service for matching bib records using specific identifiers.

This module defines the `BibMatchService`, a domain service responsible for
finding the duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.

Protocols:

`BibFetcher`
    a protocol that defines the contract for any adapter to Sierra that
    is capable of retrieving records based on identifier keys. Concrete
    implementations of this protocol are defined in the infrastructure layer.

Classes:

`BibMatchService`
    a domain service that encapsulates the logic for comparing a `DomainBib`
    against records retrieved from Sierra. This service is agnostic to infrastructure
    details, delegating data access to the injected `BibFetcher` interface.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from overload_web.domain.models import model

logger = logging.getLogger(__name__)


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that can fetch bib records from Sierra based on an identifier.

    This abstraction allows the `BibMatchService` to remain decoupled from any specific
    data source or API. Implementations may a REST APIs, BPL's Solr service, NYPL's
    Platform serivce, or other systems.
    """

    def get_bibs_by_id(self, value: str | int, key: str) -> List[Dict[str, Any]]: ...

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """


class BibMatchService:
    """
    Domain service for finding the best-match for a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services selects a record as the best match if if has the most attribute matches of all candidate records.
    """

    def __init__(self, fetcher: BibFetcher, matchpoints: Optional[List[str]] = None):
        """
        Initialize the match service with a fetcher and optional matchpoints.

        Args:
            fetcher: An injected adapter or client that provides candidate bibs.
            matchpoints: ordered list of fields to use for matching.
        """
        self.fetcher = fetcher
        self.matchpoints = matchpoints or [
            "oclc_number",
            "isbn",
            "issn",
            "bib_id",
            "upc",
        ]

    def _select_best_match(
        self, bib_to_match: model.DomainBib, candidates: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Compare a `DomainBib` to a list of candidate bibs and select the best match.

        Args:
            bib_to_match: the bib record to match as a `DomainBib`.
            candidates: a list of candidate bib records as dicts

        Returns:
            the Sierra Bib ID of the best candidate, or `None` if no match
        """
        max_matched_points = -1
        best_match_bib_id = None
        for bib in candidates:
            matched_points = 0
            for attr in self.matchpoints:
                if getattr(bib_to_match, attr) == bib.get(attr):
                    matched_points += 1

            if matched_points > max_matched_points:
                max_matched_points = matched_points
                best_match_bib_id = bib.get("bib_id")

        return best_match_bib_id

    def find_best_match(self, bib: model.DomainBib) -> Optional[str]:
        """
        Attempt to find the best-match in Sierra for a given `DomainBib`.

        The method queries the fetcher obj for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            bib: The bibliographic record to match against Sierra.

        Returns:
            the bib_id of the best match, or `None` if no candidates found.
        """
        for key in self.matchpoints:
            value = getattr(bib, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                return self._select_best_match(bib_to_match=bib, candidates=candidates)
        return None
