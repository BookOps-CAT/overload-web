"""Domain service for matching incoming records against Sierra.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.
"""

from __future__ import annotations

import logging
from abc import ABC
from typing import Protocol, runtime_checkable

from overload_web.domain.errors import OverloadError
from overload_web.domain.models import bibs, sierra_responses

logger = logging.getLogger(__name__)


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that searches Sierra for bib records based on an identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[sierra_responses.BaseSierraResponse]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value pair.

    Args:
        value: The identifier value to search by (eg. "9781234567890").
        key: The field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of `BaseSierraResponse` objects representing candidate matches.
    """


class BibMatcher(ABC):
    """
    Domain service for retrieving records from Sierra that match a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services queries Sierra
    using an injected `BibFetcher` object and if any results are returned they are
    passed to the `ReviewedResults` class to selects the best match for the given
    record. The service returns the bib ID of the best match or `None` if no candidates
    were found.
    """

    def __init__(self, fetcher: BibFetcher) -> None:
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

        This method queries the fetcher object for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            record:
                The bibliographic record to match against Sierra represented as a
                `DomainBib` object.
            matchpoints:
                a dictionary containing matchpoints and their priority e.g.
                `{"primary_matchpoint": "isbn", "secondarty_matchpoint": "oclc_number"}`
        Returns:
            a list of the record's matches as `BaseSierraResponse` objects
        """
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
    ) -> list[sierra_responses.BaseSierraResponse]:
        """
        Match an order-level bibliographic record against Sierra.

        Args:
            record:
                A parsed bibliographic record as a `DomainBib` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching.

        Returns:
            A `MatchContext` object containing a processed record as
            a `DomainBib` object and its associated matches as
            `BaseSierraResponse` objects
        """
        responses: list[sierra_responses.BaseSierraResponse] = self._match_bib(
            record=record, matchpoints=matchpoints
        )
        return responses

    def match_full_record(
        self, record: bibs.DomainBib
    ) -> list[sierra_responses.BaseSierraResponse]:
        """
        Match a full-level bibliographic record against Sierra.

        Args:
            record:
                A parsed bibliographic record as a `DomainBib` object.

        Returns:
            A `MatchContext` object containing a processed record as a
            `DomainBib` object and its associated matches as `BaseSierraResponse`

        Raises:
            OverloadError: if the value of a record's `vendor_info` attribute is None.
        """
        if record.vendor_info is None:
            raise OverloadError("Vendor index required for cataloging workflow.")
        responses: list[sierra_responses.BaseSierraResponse] = self._match_bib(
            record=record, matchpoints=record.vendor_info.matchpoints
        )
        return responses
