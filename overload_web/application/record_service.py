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

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.bib_records.domain_services import (
    attacher,
    matcher,
    parser,
    serializer,
)

logger = logging.getLogger(__name__)


class RecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        collection: str,
        reviewer: marc_protocols.ResultsReviewer,
        bib_fetcher: marc_protocols.BibFetcher,
        mapper: marc_protocols.BibMapper,
        updater: marc_protocols.BibUpdater,
    ):
        """
        Initialize `RecordProcessingService`.

        Args:
            attacher:
                A `marc_protocols.ResultsReviewer` object
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            collection:
                The collection whose records are to be processed as a str.
            mapper:
                A `marc_protocols.BibMapper` object
            updater:
                A `marc_protocols.BibUpdater` object
        """
        self.collection = collection
        self.attacher = attacher.BibAttacher(reviewer=reviewer)
        self.matcher = matcher.BibMatcher(fetcher=bib_fetcher)
        self.parser = parser.BibParser(mapper=mapper)
        self.serializer = serializer.BibSerializer(serializer=updater)

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
        matched_records = self.matcher.match(
            records=parsed_records,
            matchpoints=matchpoints,
            record_type=record_type.value,
        )
        attached_records = self.attacher.attach(
            responses=matched_records, record_type=record_type.value
        )
        updated_records = self.serializer.update(
            records=attached_records,
            template_data=template_data,
            record_type=record_type.value,
        )
        output = self.serializer.serialize(updated_records)
        return output
