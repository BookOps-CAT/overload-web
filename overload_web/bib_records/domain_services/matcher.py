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
from typing import Literal, Optional, overload

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

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

    def __init__(self, fetcher: marc_protocols.BibFetcher) -> None:
        """
        Initialize the match service with a fetcher.

        Args:
            fetcher: An injected `BibFetcher` that provides candidate bibs.
        """
        self.fetcher = fetcher

    def match_bib(
        self, record: bibs.DomainBib, matchpoints: dict[str, str]
    ) -> list[bibs.BaseSierraResponse]:
        """
        Attempt to find the best-match in Sierra for a given bib record.

        The method queries the fetcher obj for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            record:
                The bibliographic record to match against Sierra represented as a
                `bibs.DomainBib` object.
            matchpoints:
                a dictionary containing matchpoints
        Returns:
            the bib id for the best match as a string or `None` if no candidates found
        """
        for priority, key in matchpoints.items():
            value = getattr(record, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                return candidates
        return []

    def _match_full_bib(self, record: bibs.DomainBib) -> list[bibs.BaseSierraResponse]:
        if not record.vendor_info:
            raise OverloadError("Vendor index required for cataloging workflow.")
        return self.match_bib(record=record, matchpoints=record.vendor_info.matchpoints)

    def _match_order_bib(
        self, record: bibs.DomainBib, matchpoints: Optional[dict[str, str]] = None
    ) -> list[bibs.BaseSierraResponse]:
        if not matchpoints:
            raise OverloadError(
                "Matchpoints from order template required for acquisition "
                "or selection workflow."
            )
        return self.match_bib(record=record, matchpoints=matchpoints)

    @overload
    def match(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.SELECTION],
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.MatcherResponse]: ...  # pragma: no branch

    @overload
    def match(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.CATALOGING],
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.MatcherResponse]: ...  # pragma: no branch

    @overload
    def match(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.ACQUISITIONS],
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.MatcherResponse]: ...  # pragma: no branch

    def match(
        self,
        records: list[bibs.DomainBib],
        record_type: bibs.RecordType,
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.MatcherResponse]:
        """
        Match bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            record_type:
                The type of record as an Literal value from bibs.RecordType.

        Returns:
            A list of processed records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            match record_type:
                case bibs.RecordType.CATALOGING:
                    matches = self._match_full_bib(record=record)
                case _:
                    matches = self._match_order_bib(
                        record=record, matchpoints=matchpoints
                    )
            out.append(bibs.MatcherResponse(bib=record, matches=matches))
        return out
