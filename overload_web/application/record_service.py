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
from typing import Any, BinaryIO

from overload_web.bib_records.domain_services import matcher, parser
from overload_web.bib_records.infrastructure import marc, sierra

logger = logging.getLogger(__name__)


class RecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self, library: str, collection: str, record_type: str, rules: dict[str, Any]
    ):
        """
        Initialize `RecordProcessingService`.

        Args:
            library:
                The library whose records are to be processed as a str.
            collection:
                The collection whose records are to be processed as a str.
            record_type:
                The type of records to be processed (full or order-level) as a str.
            rules:
                A dictionary containing the marc mapping and vendor rules to be used
                when processing records.
        """
        self.collection = collection
        self.matcher = matcher.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library),
            record_type=record_type,
            attacher=marc.BookopsMarcUpdater(rules=rules["updater_rules"]),
        )
        self.parser = parser.BibParser(
            mapper=marc.BookopsMarcMapper(rules=rules["mapper_rules"]),
            vendor_identifier=marc.BookopsMarcVendorIdentifier(
                rules=rules["vendor_rules"][library.casefold()]
            ),
            reader=marc.BookopsMarcReader(library=library),
        )

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        template_data: dict[str, Any],
        matchpoints: dict[str, Any],
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
        matched_records = self.matcher.match_and_attach(
            parsed_records, matchpoints=matchpoints, template_data=template_data
        )
        output = self.parser.serialize(matched_records)
        return output
