"""Dependency injection for record processing services."""

import logging
from typing import Annotated, Any, Generator

from fastapi import Depends, Form

from overload_web.application.services import record_service
from overload_web.infrastructure.config import loader
from overload_web.infrastructure.marc import engine
from overload_web.infrastructure.sierra import clients

logger = logging.getLogger(__name__)


def get_marc_engine_config(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    constants: Annotated[dict[str, Any], Depends(loader.load_config)],
    record_type: Annotated[str, Form(...)],
) -> engine.MarcEngineConfig:
    return loader.marc_engine_config_from_constants(
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


def get_pvf_handler(
    fetcher: Annotated[clients.SierraBibFetcher, Depends(get_fetcher)],
    analyzer: Annotated[
        record_service.match_analysis.MatchAnalyzer, Depends(get_match_analyzer)
    ],
    config: Annotated[engine.MarcEngineConfig, Depends(get_marc_engine_config)],
) -> Generator[record_service.ProcessingHandler, None, None]:
    """Create an full-record processing service with injected dependencies."""
    yield record_service.ProcessingHandler(
        fetcher=fetcher,
        analyzer=analyzer,
        engine=engine.MarcEngine(rules=config),
    )
