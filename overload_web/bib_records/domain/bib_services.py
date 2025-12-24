"""Domain service for parsing, matching, and updating bib records.

This module defines the `BibMatcher`, a domain service responsible for
finding duplicate records in Sierra for a `DomainBib`. Matching is based on
specific identifiers such as OCLC number, ISBN, or Sierra Bib ID.

Classes:

`BibAttacher`
    a domain service that reviews lists of responses from Sierra and attaches
    the appropriate bib id to an incoming record. This service delegates the
    logic used to determine which matched record is the best match to the injected
    `ResultsReviewer` interface which wraps logic that is based on the record type,
    library system, and collection.

`BibMatcher`
    a domain service that encapsulates the logic for comparing a `DomainBib`
    against records retrieved from Sierra. This service delegates data access
    to the injected `BibFetcher` interface which wraps a client used for fetching
    data from Sierra. The service uses the `ReviewedResults` class to evaluate
    candidate records and determine the best match.

`BibParser`
    a domain service that encapsulates logic for parsing a MARC record to a
    `DomainBib` object. This service delegates data access to the injected
    `BibMapper` interface which contains the logic for mapping a record to
    a domain object.

`BibSerializer`
    a domain service that outputs `DomainBib` objects to binary data.

`BibRecordUpdater`
    a domain service that updates records using an injected `BibUpdateStrategy`.
"""

from __future__ import annotations

import io
import logging
from typing import Any, BinaryIO, Optional

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class BibAttacher:
    def __init__(self, reviewer: marc_protocols.ResultsReviewer) -> None:
        self.reviewer = reviewer

    def attach(self, responses: list[bibs.MatcherResponse]) -> list[bibs.DomainBib]:
        out = []
        for response in responses:
            bib_id = self.reviewer.review_results(
                input=response.bib, results=response.matches
            )
            response.bib.bib_id = bib_id
            out.append(response.bib)
        return out


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
            fetcher: An injected `BibFetcher` that retrieves candidate bibs.
        """
        self.fetcher = fetcher

    def _get_matchpoints(
        self, record: bibs.DomainBib, matchpoints: dict[str, str] | None
    ) -> dict[str, str]:
        """
        Get matchpoints to be used in query based on type of record.

        Args:
            record:
                The bibliographic record that will be matched against Sierra
                represented as a `bibs.DomainBib` object.
            matchpoints:
                an optional dictionary containing matchpoints
        Returns:
            a dictionary containing the matchpoints to be used when matching the
            bib record.
        Raises:
            OverloadError: if the record is to be processed using the cataloging
            workflow and the record does not contain a `VendorInfo` obj with matchpoints
            or if no matchpoints were passed to the `BibMatcher.match()` method but
            the record is to be processed using the acquisitions or selection workflow.
        """
        if record.record_type.value == "cat":
            if record.vendor_info is None:
                raise OverloadError("Vendor index required for cataloging workflow.")
            return record.vendor_info.matchpoints
        if not matchpoints:
            raise OverloadError(
                "Matchpoints from order template required for acquisition "
                "or selection workflow."
            )
        return matchpoints

    def _match_bib(
        self, record: bibs.DomainBib, matchpoints: dict[str, str]
    ) -> list[bibs.BaseSierraResponse]:
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
            matchpoints = self._get_matchpoints(record=record, matchpoints=matchpoints)
            matches: list[bibs.BaseSierraResponse] = self._match_bib(
                record=record, matchpoints=matchpoints
            )
            out.append(bibs.MatcherResponse(bib=record, matches=matches))
        return out


class BibParser:
    def __init__(self, mapper: marc_protocols.BibMapper) -> None:
        self.mapper = mapper

    def parse(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Method used to build `DomainBib` objects for MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        reader = self.mapper.get_reader(data)
        for record in reader:
            bib_dict = self.mapper.map_data(record)

            if bib_dict.get("record_type") == "cat":
                vendor_info = self.mapper.identify_vendor(record)
                bib_dict["vendor_info"] = bibs.VendorInfo(**vendor_info)
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))

        return parsed


class BibSerializer:
    """Domain service for writing a `DomainBib` to MARC binary."""

    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Serialize a list of `bibs.DomainBib` objects into a binary MARC stream.

        Args:
            records: a list of records as `bibs.DomainBib` objects

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.__dict__}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data


class BibRecordUpdater:
    """
    Domain service for updating a bib record based on its record type.

    The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `BibUpdateStrategy` object.
    """

    def __init__(self, strategy: marc_protocols.BibUpdateStrategy) -> None:
        """
        Initialize the serializer service with an updater.

        Args:
            strategy: An injected `BibUpdateStrategy` that updates bib records.
        """
        self.strategy = strategy

    def update(
        self,
        records: list[bibs.DomainBib],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = self.strategy.update_bib(records=records, template_data=template_data)
        return out
