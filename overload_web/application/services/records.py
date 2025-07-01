"""Process a file containing bibliographic records."""

from dataclasses import asdict
from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models
from overload_web.infrastructure.bibs import marc, sierra


class FullRecordProcessingService:
    def __init__(self, context: models.context.SessionContext):
        self.context = context
        self.parser = self._get_parser()
        self.matcher = self._get_matcher()

    def _get_parser(self) -> marc.BookopsMarcParser:
        return marc.BookopsMarcParser(
            library=models.bibs.LibrarySystem(str(self.context.library))
        )

    def _get_matcher(self) -> logic.bibs.BibMatcher:
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
        return self.parser.parse(data=data)

    def process_records(self, records: list[dto.bib.BibDTO]) -> list[dto.bib.BibDTO]:
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
        return self.parser.serialize(records=records)


class OrderRecordProcessingService:
    def __init__(
        self,
        context: models.context.SessionContext,
        template: models.templates.Template | dict[str, Any],
    ):
        self.context = context
        self.template = template if isinstance(template, dict) else asdict(template)
        self.parser = self._get_parser()
        self.matcher = self._get_matcher()

    def _get_parser(self) -> marc.BookopsMarcParser:
        return marc.BookopsMarcParser(
            library=models.bibs.LibrarySystem(str(self.context.library))
        )

    def _get_matcher(self) -> logic.bibs.BibMatcher:
        return logic.bibs.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library=str(self.context.library)),
            matchpoints=self.template.get("matchpoints", []),
        )

    def parse(self, data: BinaryIO | bytes) -> list[dto.bib.BibDTO]:
        return self.parser.parse(data=data)

    def process_records(self, records: list[dto.bib.BibDTO]) -> list[dto.bib.BibDTO]:
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
        return self.parser.serialize(records=records)
