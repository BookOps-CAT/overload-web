"""Domain service for matching incoming records against ports.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.
"""

from __future__ import annotations

import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.errors import OverloadError
from overload_web.domain.models import bibs

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
            fetcher: An injected `ports.BibFetcher` that retrieves candidate bibs.
        """
        self.fetcher = fetcher

    def _match_bib(
        self, record: bibs.DomainBib, matchpoints: dict[str, str]
    ) -> list[dict[str, Any]]:
        """
        Find all matches in Sierra for a given bib record.

        This method queries the fetcher object for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            record:
                The bibliographic record to match against Sierra represented as a
                `DomainBib` object.
            matchpoints:
                a dictionary containing matchpoints and their priority e.g.
                `{"primary_matchpoint": "isbn", "secondary_matchpoint": "oclc_number"}`
        Returns:
            A list of the record's matches as dictionaries representing Sierra
            responses, or an empty list if no matches were found.
        """
        candidates: list[dict[str, Any]]
        for matchpoint in matchpoints.values():
            if not matchpoint:
                continue
            value = getattr(record, matchpoint, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=matchpoint)
            if candidates:
                return candidates
        return []

    def match_order_record(
        self, record: bibs.DomainBib, matchpoints: dict[str, str]
    ) -> list[dict[str, Any]]:
        """
        Match an order-level bibliographic record against ports.

        Args:
            record:
                A parsed bibliographic record as a `DomainBib` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching.

        Returns:
            A list of the record's matches as dictionaries representing Sierra
            responses, or an empty list if no matches were found.
        """
        responses: list[dict[str, Any]] = self._match_bib(
            record=record, matchpoints=matchpoints
        )
        return responses

    def match_full_record(self, record: bibs.DomainBib) -> list[dict[str, Any]]:
        """
        Match a full-level bibliographic record against ports.

        Args:
            record:
                A parsed bibliographic record as a `DomainBib` object.

        Returns:
            A list of the record's matches as dictionaries representing Sierra
            responses, or an empty list if no matches were found.

        Raises:
            OverloadError: if the value of a record's `vendor_info` attribute is None.
        """
        if record.vendor_info is None:
            raise OverloadError("Vendor index required for cataloging workflow.")
        responses: list[dict[str, Any]] = self._match_bib(
            record=record, matchpoints=record.vendor_info.matchpoints
        )
        return responses
