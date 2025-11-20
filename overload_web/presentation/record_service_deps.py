import json
import logging
from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Depends, Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure import marc, sierra

logger = logging.getLogger(__name__)


@lru_cache
def load_constants() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


def record_processing_service(
    record_type: Annotated[str, Form(...)],
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    yield record_service.RecordProcessingService(
        collection=collection,
        record_type=record_type,
        bib_fetcher=sierra.SierraBibFetcher(library),
        mapper=marc.BookopsMarcMapper(rules=constants["mapper_rules"]),
        updater=marc.BookopsMarcUpdater(rules=constants["updater_rules"]),
        vendor_id=marc.BookopsMarcVendorIdentifier(
            rules=constants["vendor_rules"][library.casefold()]
        ),
        reader=marc.BookopsMarcReader(library=library),
    )
