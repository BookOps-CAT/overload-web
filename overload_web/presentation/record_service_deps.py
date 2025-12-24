import logging
from typing import Annotated, Generator

from fastapi import Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure import (
    clients,
    marc_mapper,
    marc_update_strategy,
    response_reviewer,
)

logger = logging.getLogger(__name__)


def record_processing_service(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    yield record_service.RecordProcessingService(
        review_strategy=response_reviewer.ReviewerFactory().make(
            library=library, record_type=record_type, collection=collection
        ),
        bib_fetcher=clients.FetcherFactory().make(library),
        mapper_strategy=marc_mapper.MapperFactory().make(
            record_type=record_type, library=library
        ),
        update_strategy=marc_update_strategy.MarcUpdaterFactory().make(
            record_type=record_type
        ),
        matcher_strategy=clients.MatchStrategyFactory().make(record_type=record_type),
    )
