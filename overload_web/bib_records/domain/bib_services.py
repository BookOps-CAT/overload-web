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
    a domain service that updates records using an injected `BibUpdater`
    and outputs `DomainBib` objects to binary data.
"""

from __future__ import annotations

import io
import itertools
import logging
from abc import ABC
from typing import Any, BinaryIO, Callable

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class BibReviewer:
    def __init__(self, reviewer: marc_protocols.ResultsReviewer) -> None:
        self.reviewer = reviewer

    def review_and_attach(
        self, responses: list[bibs.MatcherResponse]
    ) -> list[bibs.DomainBib]:
        out = []
        for response in responses:
            bib_id = self.reviewer.review_results(
                input=response.bib, results=response.matches
            )
            response.bib.bib_id = bib_id
            out.append(response.bib)
        return out


class BaseBibMatcher(ABC):
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


class OrderLevelBibMatcher(BaseBibMatcher):
    def match(
        self, records: list[bibs.DomainBib], matchpoints: dict[str, str]
    ) -> list[bibs.MatcherResponse]:
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
            matches: list[bibs.BaseSierraResponse] = self._match_bib(
                record=record, matchpoints=matchpoints
            )
            out.append(bibs.MatcherResponse(bib=record, matches=matches))
        return out


class FullLevelBibMatcher(BaseBibMatcher):
    def match(self, records: list[bibs.DomainBib]) -> list[bibs.MatcherResponse]:
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
            matches: list[bibs.BaseSierraResponse] = self._match_bib(
                record=record, matchpoints=record.vendor_info.matchpoints
            )
            out.append(bibs.MatcherResponse(bib=record, matches=matches))
        return out


class BaseBibParser(ABC):
    def __init__(self, mapper: marc_protocols.BibMapper) -> None:
        self.mapper = mapper

    def _parse_records(self, data: BinaryIO | bytes) -> list[tuple[dict, Any]]:
        reader = self.mapper.get_reader(data)
        parsed = []

        for record in reader:
            bib_dict = self.mapper.map_data(record)
            parsed.append((bib_dict, record))

        return parsed


class FullLevelBibParser(BaseBibParser):
    def parse(self, data: BinaryIO | bytes) -> tuple[list[bibs.DomainBib], list[str]]:
        """
        Method used to build `DomainBib` objects for full-level MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        for bib_dict, record in self._parse_records(data):
            vendor_info = self.mapper.identify_vendor(record)
            bib_dict["vendor_info"] = bibs.VendorInfo(**vendor_info)
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))
        barcodes = [i.barcodes for i in parsed]
        return (parsed, list(itertools.chain.from_iterable(barcodes)))


class OrderLevelBibParser(BaseBibParser):
    def parse(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Method used to build `DomainBib` objects for order-level MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        for bib_dict, record in self._parse_records(data):
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))

        return parsed


class BaseBibSerializer(ABC):
    """Domain service for writing a `DomainBib` to MARC binary."""

    """
    Domain service for updating a bib record based on its record type.

    The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `BibUpdater` object.
    """

    def __init__(self, updater: marc_protocols.BibUpdater) -> None:
        """
        Initialize the serializer service with an updater.

        Args:
            updater: An injected `BibUpdater` that updates bib records.
        """
        self.updater = updater
        self._order_strategies: dict[str, Callable[..., bibs.DomainBib]] = {
            "acq": updater.update_acquisitions_record,
            "sel": updater.update_selection_record,
        }

    def _update_order_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        func = self._order_strategies[str(record.record_type)]
        return func(record=record, template_data=template_data)

    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Update bibliographic records and serialize into a binary MARC stream.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.__dict__}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data


class OrderLevelBibSerializer(BaseBibSerializer):
    def update(
        self, records: list[bibs.DomainBib], template_data: dict[str, Any]
    ) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            rec = self._update_order_record(record=record, template_data=template_data)
            out.append(rec)
        return out


class FullLevelBibSerializer(BaseBibSerializer):
    def update(self, records: list[bibs.DomainBib]) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            rec = self.updater.update_cataloging_record(record=record)
            out.append(rec)
        return out
