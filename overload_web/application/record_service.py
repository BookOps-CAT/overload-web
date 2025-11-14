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

from overload_web.domain_models import bibs
from overload_web.domain_services import bib_matcher
from overload_web.infrastructure import dto, marc, sierra

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
        self.library = library
        self.collection = collection
        self.record_type = bibs.RecordType(record_type)
        self.parser = marc.BookopsMarcParser(library=self.library, rules=rules)
        self.matcher = bib_matcher.BibMatcher(sierra.SierraBibFetcher(self.library))

    def parse(self, data: BinaryIO | bytes) -> list[dto.BibDTO]:
        """
        Parse binary MARC data into `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.

        Returns:
            A list of parsed bibliographic records as `BibDTO` objects.
        """
        return self.parser.parse(data=data, library=self.library)

    def match_records(
        self,
        records: list[dto.BibDTO],
        matchpoints: dict[str, str],
    ) -> list[dto.BibDTO]:
        """
        Match bibliographic records against Sierra.

        Args:
            records:
                A list of parsed bibliographic records as `BibDTO` objects.
            matchpoints:

        Returns:
            A list of matched records as `BibDTO` objects
        """
        out = []
        for record in records:
            if not matchpoints:
                matchpoints = record.vendor_info.matchpoints
            record.domain_bib = self.matcher.match_bib(
                record.domain_bib, matchpoints, self.record_type
            )
            record.update(bib_id=record.domain_bib.bib_id)
            out.append(record)
        return out

    def update_records(
        self, records: list[dto.BibDTO], template_data: dict[str, Any] = {}
    ) -> list[dto.BibDTO]:
        """
        Update bibliographic records using vendor and template data
        to determine which fields to update.

        Args:
            records:
                A list of parsed bibliographic records as `BibDTO` objects.
            template_data:
                Order template data as a dictionary.

        Returns:
            A list of processed and updated records as `BibDTO` objects
        """
        out = []
        for record in records:
            if self.record_type == bibs.RecordType.ORDER_LEVEL:
                record.domain_bib.apply_order_template(template_data=template_data)
                rec = self.parser.update_order_record(record=record)
            rec = self.parser.update_bib_record(
                record=record, vendor_info=record.vendor_info
            )
            out.append(rec)
        return out

    def process_records(
        self,
        records: list[dto.BibDTO],
        matchpoints: dict[str, str],
        template_data: dict[str, Any] = {},
    ) -> list[dto.BibDTO]:
        """
        Match and update bibliographic records. Uses vendor and template data
        to determine which fields to update.

        Args:
            records:
                A list of parsed bibliographic records as `BibDTO` objects.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.

        Returns:
            A list of processed and updated records as `BibDTO` objects
        """
        out = []
        for record in records:
            if not matchpoints:
                matchpoints = record.vendor_info.matchpoints
            record.domain_bib = self.matcher.match_bib(
                record.domain_bib, matchpoints, self.record_type
            )
            if self.record_type == bibs.RecordType.ORDER_LEVEL:
                record.domain_bib.apply_order_template(template_data=template_data)
                rec = self.parser.update_order_record(record=record)
            rec = self.parser.update_bib_record(
                record=record, vendor_info=record.vendor_info
            )
            out.append(rec)
        return out

    def write_marc_binary(self, records: list[dto.BibDTO]) -> BinaryIO:
        """
        Serialize records into MARC binary.

        Args:
            records:  A list of parsed bibliographic records as `BibDTO` objects.

        Returns:
            MARC data as a `BinaryIO` object
        """
        return self.parser.serialize(records=records)
