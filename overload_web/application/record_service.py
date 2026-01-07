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


class FullRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: marc_protocols.BibFetcher,
        bib_mapper: marc_protocols.BibMapper,
        review_strategy: marc_protocols.BibReviewStrategy,
        context_handler: marc_protocols.MarcContextHandler,
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
            bib_updater:
                A `marc_protocols.BibUpdater` object
        """
        self.reviewer = reviewer_service.BibReviewer(strategy=review_strategy)
        self.matcher = matcher_service.FullLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parser_service.FullLevelBibParser(mapper=bib_mapper)
        self.serializer = updater_service.FullLevelBibUpdater(
            context_handler=context_handler
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
        rules: dict[str, dict[str, str]],
        context_handler: marc_protocols.MarcContextHandler,
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
            bib_updater:
                A `marc_protocols.BibUpdater` object
        """
        self.reviewer = reviewer_service.BibReviewer(strategy=review_strategy)
        self.matcher = matcher_service.OrderLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parser_service.OrderLevelBibParser(mapper=bib_mapper)
        self.serializer = updater_service.OrderLevelBibUpdater(
            rules=rules, context_handler=context_handler
        )

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        template_data: dict[str, Any],
        matchpoints: dict[str, str],
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
