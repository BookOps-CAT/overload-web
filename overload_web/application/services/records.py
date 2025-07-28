"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service contains `library`, `collection`, `record_type`, `parser`, and `matcher`
attributes. The `parser` attribute is a `BibMatcher` domain object. The `parser
attribute is a concrete implementation of the `BibParser` domain protocol.

Classes:

`RecordProcessingService`
    an application service for processing MARC records. This service can be used
    to process both full and order-level MARC records.
"""

from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models
from overload_web.infrastructure.bibs import context, marc, sierra


class RecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        library: str,
        collection: str,
        record_type: str,
        marc_mapping: dict[str, dict[str, str]],
    ):
        """
        Initialize `RecordProcessingService`.

        Args:
            library: the library whose records are to be processed
            collection: the collection whose records are to be processed
            record_type: the type of records to be processed (full or order-level)
            marc_mapping: the marc mapping to be used when processing records
        """
        self.library = models.bibs.LibrarySystem(library)
        self.collection = models.bibs.Collection(collection)
        self.record_type = models.bibs.RecordType(record_type)
        self.parser = self._get_parser(marc_mapping=marc_mapping)
        self.matcher = self._get_matcher()

    def _normalize_matchpoints(self, matchpoints: dict[str, Any] = {}) -> list[str]:
        """Normalize matchpoints to a list."""
        return [v for k, v in matchpoints.items() if v]

    def _normalize_template(self, template_data: dict[str, Any] = {}) -> dict[str, Any]:
        """Normalize template data to a dictionary."""
        return {k: v for k, v in template_data.items() if v}

    def _get_matcher(self) -> logic.bibs.BibMatcher:
        """
        Get a `BibMatcher` object for the supplied library

        Returns:
            `BibMatcher` instance.
        """
        return logic.bibs.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library=str(self.library))
        )

    def _get_parser(
        self, marc_mapping: dict[str, dict[str, str]]
    ) -> marc.BookopsMarcParser:
        """
        Get a `BookopsMarcParser` object for the supplied library.

        Returns:
            `BookopsMarcParser` instance.
        """
        return marc.BookopsMarcParser(library=self.library, marc_mapping=marc_mapping)

    def _get_vendor_template(self, bib: dto.bib.BibDTO) -> dict[str, Any]:
        vendor_id = context.VendorIdentifier(
            library=str(self.library), collection=str(self.collection)
        )
        info = vendor_id.identify_vendor(bib=bib.bib)
        return info["template"]

    def parse(self, data: BinaryIO | bytes) -> list[dto.bib.BibDTO]:
        """
        Parse binary MARC data into `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object

        Returns:
            a list of parsed bibliographic records as `BibDTO` objects
        """
        return self.parser.parse(data=data)

    def process_records(
        self, records: list[dto.bib.BibDTO], template_data: dict[str, Any] = {}
    ) -> list[dto.bib.BibDTO]:
        """
        Match and update bibliographic records. Uses vendor and template data
        to determine which fields to update.

        Args:
            records: a list of parsed bibliographic records as `BibDTO` objects.
            template_data: template data as a `Template` object or dict.

        Returns:
            a list of processed and updated records as `BibDTO` objects
        """
        processed_bibs = []
        template_dict = self._normalize_template(template_data=template_data)
        for record in records:
            matchpoints = self._normalize_matchpoints(
                template_dict.get(
                    "matchpoints",
                    self._get_vendor_template(record).get("matchpoints", []),
                )
            )
            record.domain_bib = self.matcher.match_bib(record.domain_bib, matchpoints)
            record.domain_bib.apply_template(template_data=template_dict)
            updated_bibs = self.parser.update_fields(
                record=record,
                fields=template_dict.get(
                    "bib_template",
                    self._get_vendor_template(record).get("bib_template", []),
                ),
            )
            processed_bibs.append(updated_bibs)
        return processed_bibs

    def write_marc_binary(self, records: list[dto.bib.BibDTO]) -> BinaryIO:
        """
        Serialize records into MARC binary.

        Args:
            records:  a list of parsed bibliographic records as `BibDTO` objects.

        Returns:
            MARC data as a `BinaryIO` object
        """
        return self.parser.serialize(records=records)
