"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service contains `library`, `collection`, `record_type`, `parser`, `matcher`,
`updater`, and `vendor_reviewer` attributes. The `parser` attribute is a `BibMatcher`
domain object. The `parser attribute is a concrete implementation of the `BibParser`
domain protocol.

Classes:

`RecordProcessingService`
    An application service for processing MARC records. This service can be used
    to process both full and order-level MARC records.
"""

import logging
from typing import Any, BinaryIO, Optional

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.bib_records.domain_services import matcher, parser, reviewer

logger = logging.getLogger(__name__)


class RecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        collection: str,
        bib_fetcher: marc_protocols.BibFetcher,
        mapper: marc_protocols.BibMapper,
        updater: marc_protocols.MarcUpdater,
    ):
        """
        Initialize `RecordProcessingService`.

        Args:
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            collection:
                The collection whose records are to be processed as a str.
            mapper:
                A `marc_protocols.BibMapper` object
            updater:
                A `marc_protocols.MarcUpdater` object
        """
        self.collection = collection
        self.matcher = matcher.BibMatcher(
            fetcher=bib_fetcher, attacher=updater, reviewer=reviewer.ReviewedResults()
        )
        self.parser = parser.BibParser(mapper=mapper)

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        record_type: bibs.RecordType,
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
            record_type:
                The type of record as an Literal value from bibs.RecordType.

        Returns:
            MARC data as a `BinaryIO` object
        """
        record_type = (
            bibs.RecordType(record_type)
            if isinstance(record_type, str)
            else record_type
        )
        parsed_records = self.parser.parse(data=data, record_type=record_type.value)
        matched_records = self.matcher.match_and_attach(
            records=parsed_records,
            template_data=template_data,
            matchpoints=matchpoints,
            record_type=record_type.value,
        )
        output = self.parser.serialize(matched_records)
        return output
