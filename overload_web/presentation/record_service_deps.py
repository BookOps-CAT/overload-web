import json
import logging
from typing import Annotated, Generator

from fastapi import Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure import (
    clients,
    marc_mapper,
    marc_updater,
    response_reviewer,
)

logger = logging.getLogger(__name__)


def record_processing_service(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    yield record_service.RecordProcessingService(
        review_strategy=response_reviewer.ReviewerFactory().make(
            library=library, record_type=record_type, collection=collection
        ),
        bib_fetcher=clients.FetcherFactory().make(library),
        bib_mapper=marc_mapper.BookopsMarcMapper(
            record_type=record_type, library=library, rules=constants["mapper_rules"]
        ),
        bib_updater=marc_updater.BookopsMarcUpdater(
            rules=constants, record_type=record_type
        ),
    )
