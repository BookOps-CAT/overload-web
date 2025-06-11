from typing import Any

from overload_web.application import dto, services
from overload_web.domain import logic, models, protocols
from overload_web.infrastructure.bibs import marc, sierra


def get_record_processor(
    library: str,
    matchpoints: list[str],
    template: models.templates.Template | dict[str, Any],
) -> services.records.RecordProcessingService:
    fetcher: protocols.bibs.BibFetcher = sierra.SierraBibFetcher(library=library)
    parser: protocols.bibs.MarcTransformer[dto.bib.BibDTO] = (
        marc.BookopsMarcTransformer(library=models.bibs.LibrarySystem(library))
    )
    matcher = logic.bibs.BibMatcher(fetcher=fetcher, matchpoints=matchpoints)
    return services.records.RecordProcessingService(
        matcher=matcher, parser=parser, template=template
    )
