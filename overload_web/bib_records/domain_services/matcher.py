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
from typing import Any, Literal, Optional, overload

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
    were found. The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `MarcUpdater` object.
    """

    def __init__(
        self,
        attacher: marc_protocols.BibUpdater,
        fetcher: marc_protocols.BibFetcher,
        reviewer: marc_protocols.ResultsReviewer,
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
        self.reviewer = reviewer

    def match_bib(
        self, record: bibs.DomainBib, matchpoints: dict[str, str]
    ) -> str | None:
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
                best_match = self.reviewer.review_results(record, results=candidates)
                return best_match
        return record.bib_id

    def _match_and_attach_order(
        self,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
        matchpoints: dict[str, str],
    ) -> bibs.DomainBib:
        bib_id = self.match_bib(record=record, matchpoints=matchpoints)
        record.bib_id = bib_id
        return self.attacher.update_order_record(
            record=record, template_data=template_data
        )

    def _match_and_attach_full(self, record: bibs.DomainBib) -> bibs.DomainBib:
        if not record.vendor_info:
            raise OverloadError("Vendor index required for cataloging workflow.")
        bib_id = self.match_bib(
            record=record, matchpoints=record.vendor_info.matchpoints
        )
        record.bib_id = bib_id
        return self.attacher.update_full_record(record=record)

    @overload
    def match_and_attach(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.ORDER_LEVEL],
        template_data: Optional[dict[str, Any]] = None,
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def match_and_attach(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.FULL],
        template_data: Optional[dict[str, Any]] = None,
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    def match_and_attach(
        self,
        records: list[bibs.DomainBib],
        record_type: bibs.RecordType,
        template_data: Optional[dict[str, Any]] = None,
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[bibs.DomainBib]:
        """
        Match and update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.
            record_type:
                The type of record as an Literal value from bibs.RecordType.

        Returns:
            A list of processed and updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            match record_type:
                case bibs.RecordType.FULL:
                    rec = self._match_and_attach_full(record=record)
                case bibs.RecordType.ORDER_LEVEL if (
                    not matchpoints or not template_data
                ):
                    raise OverloadError(
                        "Order template required for selection or acquisition workflow."
                    )
                case _:
                    rec = self._match_and_attach_order(
                        record=record,
                        template_data=template_data,
                        matchpoints=matchpoints,
                    )
            out.append(rec)
        return out
