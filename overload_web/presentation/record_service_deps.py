"""Dependency injection for record processing services."""

import json
import logging
from typing import Annotated, Any, Generator

from fastapi import Depends, Form

from overload_web.application import record_service
from overload_web.bib_records.infrastructure import clients, marc_mapper, marc_updater

logger = logging.getLogger(__name__)


def get_constants() -> dict[str, Any]:
    """Retrieve processing constants from JSON file."""
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


def get_fetcher(
    library: Annotated[str, Form(...)],
) -> Generator[clients.SierraBibFetcher, None, None]:
    """Create a Sierra bib fetcher service for a library."""
    yield clients.FetcherFactory().make(library)


def get_match_analyzer(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> Generator[record_service.review.MatchAnalyzer, None, None]:
    """Create a match analyzer based on library, record type, and collection."""
    yield record_service.MatchAnalyzerFactory().make(
        library=library, record_type=record_type, collection=collection
    )


def get_mapper(
    library: Annotated[str, Form(...)],
    constants: Annotated[dict[str, Any], Depends(get_constants)],
    record_type: Annotated[str, Form(...)],
) -> Generator[marc_mapper.BookopsMarcMapper, None, None]:
    """Create a MARC mapper based on library and record type."""
    yield marc_mapper.BookopsMarcMapper(
        record_type=record_type, library=library, rules=constants["mapper_rules"]
    )


def order_level_processing_service(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    mapper: Annotated[marc_mapper.BookopsMarcMapper, Depends(get_mapper)],
    reviewer: Annotated[
        record_service.review.MatchAnalyzer, Depends(get_match_analyzer)
    ],
    constants: Annotated[dict[str, Any], Depends(get_constants)],
) -> Generator[record_service.OrderRecordProcessingService, None, None]:
    """Create an order-record processing service with injected dependencies."""
    yield record_service.OrderRecordProcessingService(
        bib_fetcher=fetcher,
        bib_mapper=mapper,
        match_analyzer=reviewer,
        rules=constants,
        update_handler=marc_updater.BookopsMarcUpdateHandler(),
    )


def full_level_processing_service(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    mapper: Annotated[marc_mapper.BookopsMarcMapper, Depends(get_mapper)],
    reviewer: Annotated[
        record_service.review.MatchAnalyzer, Depends(get_match_analyzer)
    ],
) -> Generator[record_service.FullRecordProcessingService, None, None]:
    """Create an full-record processing service with injected dependencies."""
    yield record_service.FullRecordProcessingService(
        bib_fetcher=fetcher,
        bib_mapper=mapper,
        match_analyzer=reviewer,
        update_handler=marc_updater.BookopsMarcUpdateHandler(),
    )
