"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service takes a `collection`, `BibFetcher`, `BibMapper`, and `BibUpdate` as args and
has `collection`, `parser`, and `matcher` attributes. The `parser` attribute is a
`BibParser` domain object and contains a concrete implementation of the `BibMapper`
domain protocol. The `matcher` attribute is a `BibMatcher` domain object and contains
a concrete implementation of the `BibFetcher` domain protocol.

Classes:

`FullRecordProcessingService`
    An application service for processing full-level MARC records. This service can be
    used to process MARC records following the cataloging workflow.

`OrderRecordProcessingService`
    An application service for processing order-level MARC records. This service can be
    used to process records following the acquisitions or selection workflows.
"""

import logging
from typing import Any, BinaryIO

from overload_web.bib_records.domain import (
    marc_protocols,
    matcher_service,
    parser_service,
    reviewer_service,
    updater_service,
)

logger = logging.getLogger(__name__)


class ReviewStrategyFactory:
    def make(
        self, library: str, record_type: str, collection: str
    ) -> marc_protocols.BibReviewStrategy:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return reviewer_service.NYPLCatBranchReviewStrategy()
            case "cat", "nypl", "RL":
                return reviewer_service.NYPLCatResearchReviewStrategy()
            case "cat", "bpl", _:
                return reviewer_service.BPLCatReviewStrategy()
            case "sel", _, _:
                return reviewer_service.SelectionReviewStrategy()
            case _:
                return reviewer_service.AcquisitionsReviewStrategy()


class FullRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: marc_protocols.BibFetcher,
        bib_mapper: marc_protocols.BibMapper,
        review_strategy: marc_protocols.BibReviewStrategy,
        update_handler: marc_protocols.MarcUpdateHandler,
    ):
        """
        Initialize `FullRecordProcessingService`.

        Args:
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            bib_mapper:
                A `marc_protocols.BibMapper` object
            review_strategy:
                A `marc_protocols.BibReviewStrategy` object
            update_handler:
                A `marc_protocols.BibUpdater` object
        """
        self.reviewer = reviewer_service.BibReviewer(strategy=review_strategy)
        self.matcher = matcher_service.FullLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parser_service.FullLevelBibParser(mapper=bib_mapper)
        self.serializer = updater_service.FullLevelBibUpdater(
            update_handler=update_handler
        )

    def process_vendor_file(self, data: BinaryIO | bytes) -> BinaryIO:
        """
        Parse MARC records, match them against Sierra, update the records with required
        fields and write them to MARC binary.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
        Returns:
            MARC data as a `BinaryIO` object
        """
        parsed_records, barcodes = self.parser.parse(data=data)
        matched_records = self.matcher.match(records=parsed_records)
        attached_records = self.reviewer.review_and_attach(responses=matched_records)
        updated_records = self.serializer.update(records=attached_records)
        output = self.serializer.serialize(updated_records)
        return output


class OrderRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: marc_protocols.BibFetcher,
        bib_mapper: marc_protocols.BibMapper,
        review_strategy: marc_protocols.BibReviewStrategy,
        rules: dict[str, Any],
        update_handler: marc_protocols.MarcUpdateHandler,
    ):
        """
        Initialize `OrderRecordProcessingService`.

        Args:
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            bib_mapper:
                A `marc_protocols.BibMapper` object
            review_strategy:
                A `marc_protocols.BibReviewStrategy` object
            rules:
                A set of rules to be used by the `BibUpdater` as a dict
            update_handler:
                A `marc_protocols.BibUpdater` object
        """
        self.reviewer = reviewer_service.BibReviewer(strategy=review_strategy)
        self.matcher = matcher_service.OrderLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parser_service.OrderLevelBibParser(mapper=bib_mapper)
        self.serializer = updater_service.OrderLevelBibUpdater(
            rules=rules, update_handler=update_handler
        )

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
    ) -> BinaryIO:
        """
        Parse MARC records, match them against Sierra, update the records with required
        fields and write them to MARC binary.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.

        Returns:
            MARC data as a `BinaryIO` object
        """
        parsed_records = self.parser.parse(data=data)
        matched_records = self.matcher.match(
            records=parsed_records, matchpoints=matchpoints
        )
        attached_records = self.reviewer.review_and_attach(responses=matched_records)
        updated_records = self.serializer.update(
            records=attached_records, template_data=template_data
        )
        output = self.serializer.serialize(updated_records)
        return output
