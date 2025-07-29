"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service contains `library`, `collection`, `record_type`, `parser`, `matcher`,
and `marc_mapping` attributes. The `parser` attribute is a `BibMatcher` domain object.
The `parser attribute is a concrete implementation of the `BibParser` domain protocol.

Classes:

`RecordProcessingService`
    an application service for processing MARC records. This service can be used
    to process both full and order-level MARC records.
"""

import logging
from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models
from overload_web.infrastructure.bibs import marc, sierra

logger = logging.getLogger(__name__)


class RecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        library: str,
        collection: str,
        record_type: str,
        marc_mapping: dict[str, dict[str, str]],
        vendor_rules: dict[
            str, dict[str, dict[str, dict[str, dict[str, str] | list[str]]]]
        ],
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
            marc_mapping:
                The marc mapping to be used when processing records as a dictionary.
        """
        self.library = models.bibs.LibrarySystem(library)
        self.collection = models.bibs.Collection(collection)
        self.record_type = models.bibs.RecordType(record_type)
        self.parser = marc.BookopsMarcParser(self.library, marc_mapping)
        self.matcher = logic.bibs.BibMatcher(sierra.SierraBibFetcher(str(self.library)))
        self.vendor_rules = vendor_rules

    def _get_vendor_template(self, bib: dto.bib.BibDTO) -> dict[str, Any]:
        """Identify the vendor associated with a specific Bib record"""
        info = self.parser.identify_vendor(record=bib, vendor_rules=self.vendor_rules)
        return info["template"]

    def _process_record(
        self,
        record: dto.bib.BibDTO,
        matchpoints: list[str],
        order_template: dict[str, Any] = {},
    ) -> dto.bib.BibDTO:
        vendor_template = self._get_vendor_template(record)
        if not matchpoints:
            matchpoints = [
                v for k, v in vendor_template.items() if v and "_matchpoint" in k
            ]
        record.domain_bib = self.matcher.match_bib(record.domain_bib, matchpoints)
        bib_fields = vendor_template.get("bib_fields", [])
        if self.record_type == models.bibs.RecordType.ORDER_LEVEL:
            record.domain_bib.apply_order_template(template_data=order_template)
            updated_order_rec = self.parser.update_order_fields(record=record)
            return self.parser.update_bib_fields(
                record=updated_order_rec, fields=bib_fields
            )
        else:
            return self.parser.update_bib_fields(record=record, fields=bib_fields)

    def parse(self, data: BinaryIO | bytes) -> list[dto.bib.BibDTO]:
        """
        Parse binary MARC data into `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.

        Returns:
            a list of parsed bibliographic records as `BibDTO` objects.
        """
        return self.parser.parse(data=data)

    def process_records(
        self,
        records: list[dto.bib.BibDTO],
        matchpoints: list[str],
        template_data: dict[str, Any] = {},
    ) -> list[dto.bib.BibDTO]:
        """
        Match and update bibliographic records. Uses vendor and template data
        to determine which fields to update.

        Args:
            records: a list of parsed bibliographic records as `BibDTO` objects.
            template_data: order template data as a dictionary.

        Returns:
            a list of processed and updated records as `BibDTO` objects
        """
        return [
            self._process_record(
                record=i, order_template=template_data, matchpoints=matchpoints
            )
            for i in records
        ]

    def write_marc_binary(self, records: list[dto.bib.BibDTO]) -> BinaryIO:
        """
        Serialize records into MARC binary.

        Args:
            records:  a list of parsed bibliographic records as `BibDTO` objects.

        Returns:
            MARC data as a `BinaryIO` object
        """
        return self.parser.serialize(records=records)
