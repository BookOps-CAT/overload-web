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
    candidate records and determine the best match. The delegates updating of
    matched records to an injected `MarcUpdater` interface.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Protocol, TypeVar

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibVar(Protocol):
    domain_bib: bibs.DomainBib
    vendor_info: bibs.VendorInfo


T = TypeVar("T", bound=BibVar)


class BibMatcher:
    """
    Domain service for finding the best match for a bib record.

    This service compares a `DomainBib` instance against external candidates using
    specified matchpoints (e.g., ISBN, OCLC number, UPC). The services queries Sierra
    using an injected `BibFetcher` object and if any results are returned they are
    passed to the `ReviewedResults` class to selects the best match for the given
    record. The service returns the bib ID of the best match or `None` if no candidates
    were found. The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `MarcUpdater` object.
    """

    def __init__(
        self,
        attacher: marc_protocols.MarcUpdater,
        fetcher: marc_protocols.BibFetcher,
        record_type: bibs.RecordType,
    ) -> None:
        """
        Initialize the match service with a fetcher and optional matchpoints.

        Args:
            attacher: An injected `MarcUpdater` that updates bib records.
            fetcher: An injected `BibFetcher` that provides candidate bibs.
            record_type: the type of record as an enum (either `FULL` or `ORDER_LEVEL`)
        """
        self.attacher = attacher
        self.fetcher = fetcher
        self.record_type = record_type

    def match_bib(self, bib: T, matchpoints: dict[str, str]) -> bibs.BibId | None:
        """
        Attempt to find the best-match in Sierra for a given bib record.

        The method queries the fetcher obj for candidates using each matchpoint.
        The first non-empty match that returns candidates is used for comparison.

        Args:
            bib:
                The bibliographic record to match against Sierra represented as a
                `BibVar` object.
            matchpoints:
                a dictionary containing matchpoints
        Returns:
            the `BibID` for the best match or `None` if no candidates found
        """
        matchpoints = bib.vendor_info.matchpoints if not matchpoints else matchpoints
        for priority, key in matchpoints.items():
            value = getattr(bib.domain_bib, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                best_match = bibs.ReviewedResults(
                    input=bib.domain_bib,
                    record_type=self.record_type,
                    results=candidates,
                )
                return best_match.target_bib_id
        return bib.domain_bib.bib_id

    def attach_bib(
        self,
        record: T,
        bib_id: Optional[bibs.BibId],
        template_data: dict[str, Any] = {},
    ) -> T:
        """
        Update a bib record using template and using vendor data to determine
        which fields to update.

        Args:
            record:
                A bib record represented as a `BibVar` object.
            template_data:
                Order template data as a dictionary.

        Returns:
            An updated record as a `BibVar` object
        """
        record.domain_bib.bib_id = bib_id
        return self.attacher.update_record(bib=record, template_data=template_data)

    def match_and_attach(
        self,
        records: list[T],
        matchpoints: dict[str, str],
        template_data: dict[str, Any] = {},
    ) -> list[T]:
        """
        Match and update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `BibVar` objects.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.

        Returns:
            A list of processed and updated records as `BibVar` objects
        """
        out = []
        for bib in records:
            bib_id = self.match_bib(bib=bib, matchpoints=matchpoints)
            rec = self.attach_bib(
                record=bib, bib_id=bib_id, template_data=template_data
            )
            out.append(rec)
        return out
