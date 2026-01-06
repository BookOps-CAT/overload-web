import json
import logging
from typing import Annotated, Any, Generator

from fastapi import Depends, Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure import (
    clients,
    marc_mapper,
    marc_updater,
    response_reviewer,
)

logger = logging.getLogger(__name__)


def get_constants() -> dict[str, Any]:
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


def get_fetcher(
    library: Annotated[str, Form(...)],
) -> Generator[clients.SierraBibFetcher, None, None]:
    yield clients.FetcherFactory().make(library)


def get_reviewer(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> Generator[response_reviewer.marc_protocols.ResultsReviewer, None, None]:
    yield response_reviewer.ReviewerFactory().make(
        library=library, record_type=record_type, collection=collection
    )


def get_mapper(
    library: Annotated[str, Form(...)],
    constants: Annotated[dict[str, Any], Depends(get_constants)],
    record_type: Annotated[str, Form(...)],
) -> Generator[marc_mapper.BookopsMarcMapper, None, None]:
    yield marc_mapper.BookopsMarcMapper(
        record_type=record_type, library=library, rules=constants["mapper_rules"]
    )


def get_updater(
    constants: Annotated[dict[str, Any], Depends(get_constants)],
) -> Generator[marc_updater.BookopsMarcUpdater, None, None]:
    yield marc_updater.BookopsMarcUpdater(rules=constants)


def order_level_processing_service(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    mapper: Annotated[marc_mapper.BookopsMarcMapper, Depends(get_mapper)],
    updater: Annotated[marc_updater.BookopsMarcUpdater, Depends(get_updater)],
    reviewer: Annotated[
        response_reviewer.marc_protocols.ResultsReviewer, Depends(get_reviewer)
    ],
) -> Generator[record_service.OrderRecordProcessingService, None, None]:
    yield record_service.OrderRecordProcessingService(
        bib_fetcher=fetcher,
        bib_mapper=mapper,
        bib_updater=updater,
        review_strategy=reviewer,
    )


def full_level_processing_service(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    mapper: Annotated[marc_mapper.BookopsMarcMapper, Depends(get_mapper)],
    updater: Annotated[marc_updater.BookopsMarcUpdater, Depends(get_updater)],
    reviewer: Annotated[
        response_reviewer.marc_protocols.ResultsReviewer, Depends(get_reviewer)
    ],
) -> Generator[record_service.FullRecordProcessingService, None, None]:
    yield record_service.FullRecordProcessingService(
        bib_fetcher=fetcher,
        bib_mapper=mapper,
        bib_updater=updater,
        review_strategy=reviewer,
    )
