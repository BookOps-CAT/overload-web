"""Process a file containing bibliographic records.

This application service:
 - loads records from a file-like object
 - matches records against Sierra
 - updates records with results of matches
 - updates records based on a template

functions from application/services that should be moved here:
 - get_fetcher_for_library
 - match_bibs
 - read_marc_binary (this should be `load` instead)


"""

from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models, protocols


class RecordProcessingService:
    def __init__(
        self,
        parser: protocols.bibs.MarcTransformer,
        matcher: logic.bibs.BibMatcher,
        template: models.templates.Template | dict[str, Any],
    ):
        self.parser = parser
        self.matcher = matcher
        self.template = template

    def load(self, data: BinaryIO) -> list[dto.bib.BibDTO]:
        return self.parser.parse(data=data)

    def match_records(self, records: list[dto.bib.BibDTO]) -> list[dto.bib.BibDTO]:
        updated_bibs = []
        for record in records:
            record.domain_bib.bib_id = self.matcher.find_best_match(record.domain_bib)
            record.update_bib_fields()
            updated_bibs.append(record)
        return updated_bibs

    def update_bib(
        self, records: list[dto.bib.BibDTO], template: dict[str, Any]
    ) -> list[dto.bib.BibDTO]:
        processed_bibs = []
        for record in records:
            record.domain_bib.apply_template(template_data=template)
            record.update_order_fields()
            record.update_bib_fields(template.get("update_fields", []))
            processed_bibs.append(record)
        return processed_bibs

    def write_marc_binary(self, records: list[dto.bib.BibDTO]) -> BinaryIO:
        return self.parser.serialize(records=records)
