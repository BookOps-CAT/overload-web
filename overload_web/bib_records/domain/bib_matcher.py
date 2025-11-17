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
from typing import BinaryIO, Protocol, runtime_checkable

from overload_web.bib_records.domain import bibs, marc_protocols, responses

logger = logging.getLogger(__name__)


@runtime_checkable
class BibFetcher(Protocol):
    """
    Protocol for a service that can fetch bib records from Sierra based on an
    identifier.

    This abstraction allows the `BibMatcher` to remain decoupled from any specific
    data source or API. Implementations can include REST APIs, BPL's Solr service,
    NYPL's Platform serivce, or other systems.
    """

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[responses.FetcherResponseDict]: ...  # pragma: no branch

    """
    Retrieve candidate bib records that match a key-value identifier.

    Args:
        value: the identifier value to search by (eg. "9781234567890").
        key: the field name corresponding to the identifier (eg. "isbn").

    Returns:
        a list of bib-like dicts representing candidate matches.
    """


class BibParser:
    """Domain service for parsing bib records from MARC data."""

    def __init(self, parser: marc_protocols.MarcParser) -> None:
        """
        Initialize the bib parser service.

        Args:
            parser: An injected `MarcParser` that handles MARC parsing.
        """
        self.parser = parser

    def parse(self, data: bytes | BinaryIO, library: str) -> list:
        """
        Parse MARC data into a list of `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
            library: The library code for which to parse the records.

        Returns:
            A list of parsed bibliographic records as `BibDTO` objects.
        """
        return self.parser.parse(data=data, library=library)


class BibMatcher:
    """
    Domain service for finding the best match for a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services selects a
    record as the best match if it has the most attribute matches of all candidate
    records.
    """

    def __init__(self, fetcher: BibFetcher):
        """
        Initialize the match service with a fetcher and optional matchpoints.

        Args:
            fetcher: An injected `BibFetcher` that provides candidate bibs.
        """
        self.fetcher = fetcher

    def _select_best_match(
        self,
        bib_to_match: bibs.DomainBib,
        candidates: list[responses.FetcherResponseDict],
        record_type: bibs.RecordType,
    ) -> bibs.ReviewedResults:
        """
        Compare a `DomainBib` to a list of candidate bibs and select the best match.

        Args:
            bib_to_match: the bib record to match as a `DomainBib`.
            candidates: a list of candidate bib records as dicts
            matchpoints: a dictionary containing matchpoints
            record_type: the type of record as an enum (either `FULL` or `ORDER_LEVEL`)

        Returns:
            The results as a `bibs.ReviewedResults` object.
        """
        reviewed_results = bibs.ReviewedResults(
            input=bib_to_match, record_type=record_type, results=candidates
        )
        return reviewed_results

    def match_bib(
        self,
        bib: bibs.DomainBib,
        matchpoints: dict[str, str],
        record_type: bibs.RecordType,
    ) -> bibs.DomainBib:
        """
        Attempt to find the best-match in Sierra for a given `DomainBib`.

        The method queries the fetcher obj for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            bib: The bibliographic record to match against Sierra.
            matchpoints: a dictionary containing matchpoints
            record_type: the type of record as an enum (either `FULL` or `ORDER_LEVEL`)
        Returns:
            the `DomainBib` object with an updated bib_id (either the best match or
            `None` if no candidates found)
        """
        for priority, key in matchpoints.items():
            value = getattr(bib, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                bib.bib_id = self._select_best_match(
                    bib_to_match=bib, candidates=candidates, record_type=record_type
                ).target_bib_id
                return bib
        return bib
