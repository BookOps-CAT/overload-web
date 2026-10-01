"""Application service for matching incoming records against ports.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from overload_web.domain.pvf import matching, models, ports

logger = logging.getLogger(__name__)


class BibMatcher:
    """
    Domain service for retrieving records from Sierra that match a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services queries Sierra
    using an injected `BibFetcher` object and if any results are returned they are
    passed to the `BaseSierraResponse` class to selects the best match for the given
    record. The service returns the bib ID of the best match or `None` if no candidates
    were found.
    """

    def __init__(self, fetcher: ports.BibFetcher) -> None:
        """
        Initialize the match service with a fetcher.

        Args:
            fetcher:
                An injected `ports.BibFetcher` that retrieves candidate bibs
                from Sierra.
        """
        self.fetcher = fetcher

    def _match_bib(
        self, matchpoints: dict[str, str], record: models.DomainBib
    ) -> Sequence[dict[str, Any]]:
        """
        Find all matches in Sierra for a given bib record.

        This method queries the fetcher object for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            matchpoints:
                a dictionary containing matchpoints and their priority e.g.
                `{"primary_matchpoint": "isbn", "secondary_matchpoint": "bib_id"}`
            record:
                The bibliographic record to match against Sierra represented as a
                `DomainBib` object.
        Returns:
            A list of the record's matches as dictionaries representing Sierra
            responses, or an empty list if no matches were found.
        """
        candidates: Sequence[dict[str, Any]]
        for matchpoint in matchpoints.values():
            if not matchpoint:
                continue
            value = getattr(record, matchpoint, None)
            if not value:
                continue
            else:
                candidates = self.fetcher.get_bibs_by_id(value=value, key=matchpoint)
                if candidates:
                    return candidates
        return []

    def match_order_record(
        self, matchpoints: dict[str, str], record: models.DomainBib
    ) -> Sequence[dict[str, Any]]:
        """
        Match an order-level bibliographic record against Sierra.

        Args:
            matchpoints:
                a dictionary containing matchpoints and their priority e.g.
                `{"primary_matchpoint": "isbn", "secondary_matchpoint": "bib_id"}`
            record:
                The bibliographic record to match against Sierra represented as a
                `DomainBib` object.
        Returns:
            A list of the record's matches as dictionaries representing Sierra
            responses, or an empty list if no matches were found.
        """
        responses: Sequence[dict[str, Any]] = self._match_bib(
            record=record, matchpoints=matchpoints
        )
        return responses

    def match_full_record(self, record: models.DomainBib) -> Sequence[dict[str, Any]]:
        """
        Match a full-level bibliographic record against Sierra.

        Args:
            record:
                A parsed bibliographic record as a `DomainBib` object.

        Returns:
            A list of the record's matches as dictionaries representing Sierra
            responses, or an empty list if no matches were found.

        Raises:
            ValueError: if the value of a record's `vendor_info` attribute is None.
        """
        if record.vendor_info is None:
            raise ValueError("Vendor index required for cataloging workflow.")
        responses: Sequence[dict[str, Any]] = self._match_bib(
            record=record, matchpoints=record.vendor_info.matchpoints
        )
        return responses

    def review_matches(
        self, bib: models.DomainBib, matches: Sequence[dict[str, Any]]
    ) -> matching.MatchAnalysis:
        """
        Review and categorize match candidates returned from Sierra.

        Args:
            bib:
                A parsed bibliographic record as a `DomainBib` object.
            matches:
                A list of dictionaries representing results from Sierra.

        Returns:
            A `MatchAnalysis` object containing classified matches.
        """
        analyzer = matching.MatchAnalyzerFactory.make(
            library=bib.library, record_type=bib.record_type, collection=bib.collection
        )
        candidates = analyzer.classify_matches(record=bib, matches=matches)
        return analyzer.analyze(record=bib, candidates=candidates)
