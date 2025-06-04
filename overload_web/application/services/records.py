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

from overload_web.application.dto import bib_dto
from overload_web.domain.logic import bib_matcher
from overload_web.domain.models import templates
from overload_web.domain.protocols import parsers


class ProcessRecordService:
    def __init__(
        self,
        parser: parsers.MarcTransformer,
        matcher: bib_matcher.BibMatchService,
        template: templates.Template | dict[str, Any],
    ):
        self.parser = parser
        self.matcher = matcher
        self.template = template

    def load(self, data: BinaryIO) -> list[bib_dto.BibDTO]:
        return self.parser.parse(data=data)

    def match_records(self, records: list[bib_dto.BibDTO]) -> list[bib_dto.BibDTO]:
        updated_bibs = []
        for bib in records:
            bib.domain_bib.bib_id = self.matcher.find_best_match(bib.domain_bib)
            bib.update_bib_fields()
            updated_bibs.append(bib)
        return updated_bibs

    def update_bib_fields(
        self, records: list[bib_dto.BibDTO], template: dict[str, Any]
    ) -> list[bib_dto.BibDTO]:
        processed_bibs = []
        for bib in records:
            bib.domain_bib.apply_template(template_data=template)
            bib.update_order_fields()
            processed_bibs.append(bib)
        return processed_bibs

    def write_marc_binary(self, records: list[bib_dto.BibDTO]) -> BinaryIO:
        return self.parser.serialize(records=records)
