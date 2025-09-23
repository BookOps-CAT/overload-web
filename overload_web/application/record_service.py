"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service contains `library`, `collection`, `record_type`, `parser`, `matcher`,
and `marc_mapping` attributes. The `parser` attribute is a `BibMatcher` domain object.
The `parser attribute is a concrete implementation of the `BibParser` domain protocol.

Classes:

`RecordProcessingService`
    An application service for processing MARC records. This service can be used
    to process both full and order-level MARC records.
"""

import logging
from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models
from overload_web.infrastructure.bibs import marc, sierra, vendor

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
        self.record_type = models.bibs.RecordType(record_type)
        self.parser = marc.BookopsMarcParser(marc_mapping=rules["bookops_marc_mapping"])
        self.matcher = logic.bibs.BibMatcher(sierra.SierraBibFetcher(self.library))
        self.updater = marc.BookopsMarcUpdater(rules["order_subfield_mapping"])
        self.vendor_reviewer = vendor.VendorIdentifier(
            vendor_tags=rules["vendor_tags"][library.casefold()],
            vendor_info=rules["vendor_info"][library.casefold()],
        )

    def parse(self, data: BinaryIO | bytes) -> list[dto.BibDTO]:
        """
        Parse binary MARC data into `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.

        Returns:
            A list of parsed bibliographic records as `BibDTO` objects.
        """
        return self.parser.parse(data=data, library=self.library)

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
            vendor_info = self.vendor_reviewer.vendor_id(record.bib)
            if not matchpoints:
                matchpoints = vendor_info.matchpoints
            record.domain_bib = self.matcher.match_bib(record.domain_bib, matchpoints)
            if self.record_type == models.bibs.RecordType.ORDER_LEVEL:
                record.domain_bib.apply_order_template(template_data=template_data)
                rec = self.updater.update_order_record(record=record)
            rec = self.updater.update_bib_record(record=record, vendor_info=vendor_info)
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
