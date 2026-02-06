"""Dependency injection for record processing services."""

import logging
from typing import Annotated, Any, Generator

from fastapi import Depends, Form

from overload_web.application.services import record_service
from overload_web.infrastructure.config import loader
from overload_web.infrastructure.marc import marc_mapper, update_engine
from overload_web.infrastructure.sierra import clients

logger = logging.getLogger(__name__)


def get_bib_mapper_config(
    library: Annotated[str, Form(...)],
    constants: Annotated[dict[str, Any], Depends(loader.load_config)],
    record_type: Annotated[str, Form(...)],
) -> marc_mapper.BibMapperConfig:
    return loader.mapper_config_from_constants(
        constants=constants, library=library, record_type=record_type
    )


def get_bib_engine_config(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    constants: Annotated[dict[str, Any], Depends(loader.load_config)],
    record_type: Annotated[str, Form(...)],
) -> update_engine.BibEngineConfig:
    return loader.engine_config_from_constants(
        constants=constants,
        library=library,
        collection=collection,
        record_type=record_type,
    )


def get_fetcher(
    library: Annotated[str, Form(...)],
) -> Generator[clients.SierraBibFetcher, None, None]:
    """Create a Sierra bib fetcher service for a library."""
    yield clients.FetcherFactory().make(library)


def get_match_analyzer(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> Generator[record_service.match_analysis.MatchAnalyzer, None, None]:
    """Create a match analyzer based on library, record type, and collection."""
    yield record_service.MatchAnalyzerFactory().make(
        library=library, record_type=record_type, collection=collection
    )


def order_level_processing_service(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    analyzer: Annotated[
        record_service.match_analysis.MatchAnalyzer, Depends(get_match_analyzer)
    ],
    mapper_config: Annotated[
        marc_mapper.BibMapperConfig, Depends(get_bib_mapper_config)
    ],
    update_engine_config: Annotated[
        update_engine.BibEngineConfig, Depends(get_bib_engine_config)
    ],
) -> Generator[record_service.OrderRecordProcessingService, None, None]:
    """Create an order-record processing service with injected dependencies."""
    yield record_service.OrderRecordProcessingService(
        bib_fetcher=fetcher,
        analyzer=analyzer,
        bib_mapper=marc_mapper.MarcMapper(rules=mapper_config),
        updater=update_engine.BibUpdateEngine(config=update_engine_config),
    )


def full_level_processing_service(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    analyzer: Annotated[
        record_service.match_analysis.MatchAnalyzer, Depends(get_match_analyzer)
    ],
    mapper_config: Annotated[
        marc_mapper.BibMapperConfig, Depends(get_bib_mapper_config)
    ],
    update_engine_config: Annotated[
        update_engine.BibEngineConfig, Depends(get_bib_engine_config)
    ],
) -> Generator[record_service.FullRecordProcessingService, None, None]:
    """Create an full-record processing service with injected dependencies."""
    yield record_service.FullRecordProcessingService(
        bib_fetcher=fetcher,
        analyzer=analyzer,
        bib_mapper=marc_mapper.MarcMapper(rules=mapper_config),
        updater=update_engine.BibUpdateEngine(config=update_engine_config),
    )
