"""Domain service for matching bib records using specific identifiers.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.

Classes:

`BibMatcher`
    a domain service that encapsulates the logic for comparing a `DomainBib`
    against records retrieved from Sierra. This service delegates data access
    to the injected `BibFetcher` interface which wraps a client used for fetching
    data from Sierra. The service uses the `ReviewedResults` class to evaluate
    candidate records and determine the best match.
"""

from __future__ import annotations

import logging
from typing import Optional

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibMatcher:
    """
    Domain service for finding the best match for a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services queries Sierra
    using an injected `BibFetcher` object and if any results are returned they are
    passed to the `ReviewedResults` class to selects the best match for the given
    record. The service returns the bib ID of the best match or `None` if no candidates
    were found.
    """

    def __init__(
        self,
        fetcher: marc_protocols.BibFetcher,
        strategy: marc_protocols.BibMatcherStrategy,
    ) -> None:
        """
        Initialize the match service with a fetcher.

        Args:
            fetcher:
                An injected `BibFetcher` that provides candidate bibs.
            strategy:
                An injected `BibMatcherStrategy` that provides strategy for matching.
        """
        self.fetcher = fetcher
        self.strategy = strategy

    def match(
        self,
        records: list[bibs.DomainBib],
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.MatcherResponse]:
        """
        Match bibliographic records.

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
            matches: list[bibs.BaseSierraResponse] = self.strategy.match_bib(
                record=record, matchpoints=matchpoints, fetcher=self.fetcher
            )
            out.append(bibs.MatcherResponse(bib=record, matches=matches))
        return out
