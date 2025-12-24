"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service takes a `collection`, `BibFetcher`, `BibMapper`, and `BibUpdate` as args and
has `collection`, `parser`, and `matcher` attributes. The `parser` attribute is a
`BibParser` domain object and contains a concrete implementation of the `BibMapper`
domain protocol. The `matcher` attribute is a `BibMatcher` domain object and contains
a concrete implementation of the `BibFetcher` domain protocol.

Classes:

`RecordProcessingService`
    An application service for processing MARC records. This service can be used
    to process both full and order-level MARC records.
"""

import logging
from typing import Any, BinaryIO, Optional

from overload_web.bib_records.domain import bib_services

logger = logging.getLogger(__name__)


class RecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: bib_services.marc_protocols.BibFetcher,
        mapper_strategy: bib_services.marc_protocols.BibMapper,
        review_strategy: bib_services.marc_protocols.ResultsReviewer,
        update_strategy: bib_services.marc_protocols.BibUpdateStrategy,
    ):
        """
        Initialize `RecordProcessingService`.

        Args:
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            mapper_strategy:
                A `marc_protocols.BibMapper` object
            review_strategy:
                A `marc_protocols.ResultsReviewer` object
            update_strategy:
                A `marc_protocols.BibUpdateStrategy` object
        """
        self.attacher = bib_services.BibAttacher(reviewer=review_strategy)
        self.matcher = bib_services.BibMatcher(fetcher=bib_fetcher)
        self.parser = bib_services.BibParser(mapper=mapper_strategy)
        self.updater = bib_services.BibRecordUpdater(strategy=update_strategy)
        self.serializer = bib_services.BibSerializer()

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        template_data: Optional[dict[str, Any]] = None,
        matchpoints: Optional[dict[str, str]] = None,
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
        attached_records = self.attacher.attach(responses=matched_records)
        updated_records = self.updater.update(
            records=attached_records, template_data=template_data
        )
        output = self.serializer.serialize(updated_records)
        return output
