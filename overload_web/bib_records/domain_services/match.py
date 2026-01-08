"""Domain service for matching.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.
"""

from __future__ import annotations

import logging
from abc import ABC

from overload_web.bib_records.domain_models import (
    bibs,
    marc_protocols,
    sierra_responses,
)
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class BibMatcher(ABC):
    """
    Domain service for finding the best match for a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services queries Sierra
    using an injected `BibFetcher` object and if any results are returned they are
    passed to the `ReviewedResults` class to selects the best match for the given
    record. The service returns the bib ID of the best match or `None` if no candidates
    were found.
    """

    def __init__(self, fetcher: marc_protocols.BibFetcher) -> None:
        """
        Initialize the match service with a fetcher.

        Args:
            fetcher: An injected `BibFetcher` that retrieves candidate bibs.
        """
        self.fetcher = fetcher

    def _match_bib(
        self, record: bibs.DomainBib, matchpoints: dict[str, str]
    ) -> list[sierra_responses.BaseSierraResponse]:
        """
        Find all matches in Sierra for a given bib record.

        The method queries the fetcher obj for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            record:
                The bibliographic record to match against Sierra represented as a
                `bibs.DomainBib` object.
            matchpoints:
                a dictionary containing matchpoints
        Returns:
            a list of the record's matches as `BaseSierraResponse` objects
        """
        for priority, key in matchpoints.items():
            value = getattr(record, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                return candidates
        return []


class OrderLevelBibMatcher(BibMatcher):
    def match(
        self, records: list[bibs.DomainBib], matchpoints: dict[str, str]
    ) -> list[sierra_responses.MatcherResponse]:
        """
        Match order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.

        Returns:
            A list of `MatcherResponse` objects containing a processed record as a
            `bibs.DomainBib` object and its associated matches as `BaseSierraResponse`
        """
        out = []
        for record in records:
            matches: list[sierra_responses.BaseSierraResponse] = self._match_bib(
                record=record, matchpoints=matchpoints
            )
            out.append(sierra_responses.MatcherResponse(bib=record, matches=matches))
        return out


class FullLevelBibMatcher(BibMatcher):
    def match(
        self, records: list[bibs.DomainBib]
    ) -> list[sierra_responses.MatcherResponse]:
        """
        Match full-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            A list of `MatcherResponse` objects containing a processed record as a
            `bibs.DomainBib` object and its associated matches as `BaseSierraResponse`

        Raises:
            OverloadError: if a record does not contain matchpoints within its
            `vendor_info` attribute.
        """
        out = []
        for record in records:
            if record.vendor_info is None:
                raise OverloadError("Vendor index required for cataloging workflow.")
            matches: list[sierra_responses.BaseSierraResponse] = self._match_bib(
                record=record, matchpoints=record.vendor_info.matchpoints
            )
            out.append(sierra_responses.MatcherResponse(bib=record, matches=matches))
        return out
