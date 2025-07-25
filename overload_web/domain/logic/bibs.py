"""Domain service for matching bib records using specific identifiers.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.

Classes:

`BibMatcher`
    a domain service that encapsulates the logic for comparing a `DomainBib`
    against records retrieved from Sierra. This service delegates data access
    to the injected `BibFetcher` interface which wraps a client used for fetching
    data from Sierra.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from overload_web.domain import models

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.domain import protocols

logger = logging.getLogger(__name__)


class BibMatcher:
    """
    Domain service for finding the best match for a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services selects a
    record as the best match if it has the most attribute matches of all candidate
    records.
    """

    def __init__(self, fetcher: protocols.bibs.BibFetcher):
        """
        Initialize the match service with a fetcher and optional matchpoints.

        Args:
            fetcher: An injected `BibFetcher` that provides candidate bibs.
            matchpoints: ordered list of fields to use for matching.
        """
        self.fetcher = fetcher

    def _select_best_match(
        self,
        bib_to_match: models.bibs.DomainBib,
        candidates: list[protocols.bibs.FetcherResponseDict],
        matchpoints: list[str],
    ) -> models.bibs.BibId | None:
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
            for attr in matchpoints:
                if getattr(bib_to_match, attr) == bib.get(attr):
                    matched_points += 1

            if matched_points > max_matched_points:
                max_matched_points = matched_points
                best_match = bib.get("bib_id")
                best_match_bib_id = (
                    models.bibs.BibId(best_match) if best_match else None
                )
        return best_match_bib_id

    def match_bib(
        self, bib: models.bibs.DomainBib, matchpoints: list[str]
    ) -> models.bibs.DomainBib:
        """
        Attempt to find the best-match in Sierra for a given `DomainBib`.

        The method queries the fetcher obj for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            bib: The bibliographic record to match against Sierra.

        Returns:
            the `DomainBib` object with an updated bib_id (either the best match or
            `None` if no candidates found)
        """
        for key in matchpoints:
            value = getattr(bib, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                bib.bib_id = self._select_best_match(
                    bib_to_match=bib, candidates=candidates, matchpoints=matchpoints
                )
                return bib
        return bib
