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

from dataclasses import asdict
from typing import Any, BinaryIO

from overload_web.application import dto
from overload_web.domain import logic, models, protocols
from overload_web.infrastructure.bibs import marc, sierra


class RecordProcessingService:
    def __init__(
        self,
        library: str,
        matchpoints: list[str],
        template: models.templates.Template | dict[str, Any],
        parser: protocols.bibs.MarcTransformer | None = None,
        matcher: logic.bibs.BibMatcher | None = None,
    ):
        self.parser = parser if parser else self._get_parser(library=library)
        self.matcher = (
            matcher
            if matcher
            else self._get_matcher(library=library, matchpoints=matchpoints)
        )
        self.template = template if isinstance(template, dict) else asdict(template)

    def _get_parser(self, library: str) -> protocols.bibs.MarcTransformer:
        return marc.BookopsMarcTransformer(library=models.bibs.LibrarySystem(library))

    def _get_matcher(
        self, library: str, matchpoints: list[str]
    ) -> logic.bibs.BibMatcher:
        return logic.bibs.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library=library), matchpoints=matchpoints
        )

    def load(self, data: BinaryIO) -> list[dto.bib.BibDTO]:
        return self.parser.parse(data=data)

    def process_records(self, records: list[dto.bib.BibDTO]) -> list[dto.bib.BibDTO]:
        processed_bibs = []
        for record in records:
            # match bib and update bib_id with matcher
            record.domain_bib = self.matcher.match_bib(record.domain_bib)

            # apply template to bib with domain service
            record.domain_bib.apply_template(template_data=self.template)

            # update MARC fields using parser
            updated_bibs = self.parser.update_fields(
                record=record, fields=self.template.get("update_fields", [])
            )
            processed_bibs.append(updated_bibs)
        return processed_bibs

    def write_marc_binary(self, records: list[dto.bib.BibDTO]) -> BinaryIO:
        return self.parser.serialize(records=records)
