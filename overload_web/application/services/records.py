"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The services each contain `context`, `parser`, and `matcher` attributes. The `parser`
attribute is a `BibMatcher` domain object. The `parser attribute is a concrete
implementation of the `BibParser` domain protocol. The `context` attribute contains
session-specific data used to instantiate the `BibParser` and `BibMatcher` objects.

Classes:

`FullRecordProcessingService`
    an applicaiton service for processing full MARC records. This service was
    previously provided in Overload by selecting 'cataloging' as the department

`OrderRecordProcessingService`
    an applicaiton service for processing order-level MARC records. This service
    was previously provided in Overload by selecting 'acquisitions' or 'selection'
    as the department.
"""

from dataclasses import asdict
from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models
from overload_web.infrastructure.bibs import marc, sierra


class FullRecordProcessingService:
    """Handles full MARC record parsing, matching, and serialization."""

    def __init__(self, context: models.context.SessionContext):
        """
        Initialize `FullRecordProcessingService`.

        Args:
            context: configuration and rules as a `SessionContext` object
        """
        self.context = context
        self.parser = self._get_parser()
        self.matcher = self._get_matcher()

    def _get_parser(self) -> marc.BookopsMarcParser:
        """
        Get a `BookopsMarcParser` parser based on library provided in
        the `SessionContext`.

        Returns:
            `BookopsMarcParser` instance.
        """
        return marc.BookopsMarcParser(
            library=models.bibs.LibrarySystem(str(self.context.library))
        )

    def _get_matcher(self) -> logic.bibs.BibMatcher:
        """
        Get a `BibMatcher` based on library and vendor_data provided in
        the `SessionContext`

        Returns:
            `BibMatcher` instance.
        """
        matchpoints = [
            self.context.vendor_data.get("primary_matchpoint"),
            self.context.vendor_data.get("secondary_matchpoint"),
            self.context.vendor_data.get("tertiary_matchpoint"),
        ]
        return logic.bibs.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library=str(self.context.library)),
            matchpoints=[i for i in matchpoints if i],
        )

    def parse(self, data: BinaryIO | bytes) -> list[dto.bib.BibDTO]:
        """
        Parse binary MARC data into `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object

        Returns:
            a list of parsed bibliographic records as `BibDTO` objects
        """
        return self.parser.parse(data=data)

    def process_records(self, records: list[dto.bib.BibDTO]) -> list[dto.bib.BibDTO]:
        """
        Match and update bibliographic records. Uses vendor data to determine which
        fields to update.

        Args:
            records: a list of parsed bibliographic records as `BibDTO` objects.

        Returns:
            a list of processed and updated records as `BibDTO` objects
        """
        update_fields = self.context.vendor_data.get("bib_template", [])
        processed_bibs = []
        for record in records:
            record.domain_bib = self.matcher.match_bib(record.domain_bib)
            updated_bibs = self.parser.update_fields(
                record=record, fields=update_fields
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


class OrderRecordProcessingService:
    """Handles order-level record  parsing, matching, and serialization."""

    def __init__(
        self,
        context: models.context.SessionContext,
        template: models.templates.Template | dict[str, Any],
    ):
        """
        Initialize `OrderRecordProcessingService` with `SessionContext` and
        `Template` objects.

        Args:
            context: configuration and rules as a `SessionContext` object
            template: Order processing template as a `Template` object or dict
        """
        self.context = context
        self.template = template if isinstance(template, dict) else asdict(template)
        self.parser = self._get_parser()
        self.matcher = self._get_matcher()

    def _get_parser(self) -> marc.BookopsMarcParser:
        """
        Get a `BookopsMarcParser` parser based on library provided in
        the `SessionContext`.

        Returns:
            `BookopsMarcParser` instance.
        """
        return marc.BookopsMarcParser(
            library=models.bibs.LibrarySystem(str(self.context.library))
        )

    def _get_matcher(self) -> logic.bibs.BibMatcher:
        """
        Get a `BibMatcher` based on library and vendor_data provided in
        the `SessionContext`

        Returns:
            `BibMatcher` instance.
        """
        return logic.bibs.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library=str(self.context.library)),
            matchpoints=self.template.get("matchpoints", []),
        )

    def parse(self, data: BinaryIO | bytes) -> list[dto.bib.BibDTO]:
        """
        Parse binary MARC data into `BibDTO` objects.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object

        Returns:
            a list of parsed bibliographic records as `BibDTO` objects
        """
        return self.parser.parse(data=data)

    def process_records(self, records: list[dto.bib.BibDTO]) -> list[dto.bib.BibDTO]:
        """
        Match and update bibliographic records. Applies the template data to all
        orders on each bib record. Uses the template data passed to the processing
        service to determine which fields to update.

        Args:
            records: a list of parsed bibliographic records as `BibDTO` objects.

        Returns:
            a list of processed and updated records as `BibDTO` objects
        """
        processed_bibs = []
        for record in records:
            record.domain_bib = self.matcher.match_bib(record.domain_bib)
            record.domain_bib.apply_template(template_data=self.template)
            updated_bibs = self.parser.update_fields(
                record=record, fields=self.template.get("update_fields", [])
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
