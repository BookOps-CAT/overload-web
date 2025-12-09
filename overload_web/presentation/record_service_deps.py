import json
import logging
from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure.marc import mapper, update_strategy
from overload_web.bib_records.infrastructure.sierra import clients, reviewer

logger = logging.getLogger(__name__)


@lru_cache
def load_constants() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


def record_processing_service(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    yield record_service.RecordProcessingService(
        reviewer=reviewer.ReviewerFactory().make(
            library=library, record_type=record_type, collection=collection
        ),
        bib_fetcher=clients.FetcherFactory().make(library),
        mapper=mapper.MapperFactory().make(record_type=record_type, library=library),
        bib_updater=update_strategy.MarcUpdaterFactory().make(record_type=record_type),
        matcher_strategy=clients.MatchStrategyFactory().make(record_type=record_type),
    )
