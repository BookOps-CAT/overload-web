import json
import logging
from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Depends, Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure.marc import mapper, updater
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
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    yield record_service.RecordProcessingService(
        collection=collection,
        reviewer=reviewer.SierraResponseReviewer(),
        bib_fetcher=clients.SierraBibFetcher(library),
        mapper=mapper.BookopsMarcMapper(
            rules=constants["mapper_rules"], library=library
        ),
        updater=updater.BookopsMarcUpdater(rules=constants["updater_rules"]),
    )
