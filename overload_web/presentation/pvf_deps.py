"""Dependency injection functions."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Form, Request
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf import process_manager
from overload_web.bootstrap import bootstrap_message_bus
from overload_web.domain.pvf import services
from overload_web.infrastructure import (
    file_io,
    marc_handler,
    reporter,
    sierra_clients,
    unit_of_work,
)
from overload_web.presentation import schemas

logger = logging.getLogger(__name__)


def get_uri_for_engine():
    """Get the Postgres database URI from environment variables."""
    db_type = os.environ.get("DB_TYPE", "sqlite")
    user = os.environ.get("POSTGRES_USER")
    pw = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    name = os.environ.get("POSTGRES_DB")
    uri = f"{db_type}://{user}:{pw}@{host}:{port}/{name}"
    uri = uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")
    return uri


def get_engine(uri: str):
    """Build an engine for the URI."""
    engine = create_engine(uri)
    return engine


@lru_cache
def parser_rules() -> dict[str, Any]:
    """Open and cache parsing rules"""
    with open("overload_web/data/parsing_rules.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache
def updater_rules() -> dict[str, Any]:
    """Open and cache updater rules"""
    with open("overload_web/data/update_rules.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def create_db_and_tables(engine) -> None:
    """Create the database and tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


def local_file_storage() -> file_io.LocalFileStorage:
    return file_io.LocalFileStorage(base_path="temp/uploads")


def remote_file_retriever(vendor: str) -> file_io.SFTPFileRetriever:
    """Create an SFTP file retriever service."""
    return file_io.SFTPFileRetriever.create_retriever_for_vendor(vendor=vendor)


def get_report_writer() -> reporter.GoogleSheetsReporter:
    """Return a `GoogleSheetsReporter` in order to write stats to a Google Sheet."""
    return reporter.GoogleSheetsReporter()


def get_uow(request: Request) -> unit_of_work.SqlModelUnitOfWork:
    """
    Provide an un-entered Unit of Work instance.

    The UoW takes the engine and manages its own session lifecycle when
    used in a context manager, making it safe to pass to BackgroundTasks.
    """
    return unit_of_work.SqlModelUnitOfWork(engine=request.app.state.engine)


def get_fetcher(library: Annotated[str, Form(...)]) -> sierra_clients.SierraBibFetcher:
    """Create a SierraBibFetcher service for a library."""
    return sierra_clients.FetcherFactory.make(library)


def get_matcher(fetcher: Any = Depends(get_fetcher)) -> services.BibMatcher:
    """Create a BibMatcher service for a library."""
    return services.BibMatcher(fetcher=fetcher)


def get_parser(
    context: Annotated[
        schemas.ProcessingContext, Depends(schemas.ProcessingContext.from_form)
    ],
    parser_rules: Annotated[dict[str, Any], Depends(parser_rules)],
) -> services.BibParser:
    """Create a BibParser service for a library."""
    parser = marc_handler.MarcParser()
    return services.BibParser(
        handler=parser,
        bib_mapping=parser_rules["bib_mapping"],
        library=context.library,
        collection=context.collection,
        record_type=context.record_type,
        order_mapping=parser_rules["order_mapping"],
        vendor_mapping=parser_rules["vendor_mapping"],
    )


def get_updater(
    context: Annotated[
        schemas.ProcessingContext, Depends(schemas.ProcessingContext.from_form)
    ],
    updater_rules: Annotated[dict[str, Any], Depends(updater_rules)],
) -> services.BibUpdater:
    """Create a BibUpdater service for a library."""
    updater = marc_handler.MarcUpdater()
    return services.BibUpdater(
        handler=updater,
        bib_id_tag=updater_rules["bib_id_tag"][context.library],
        library=context.library,
        order_mapping=updater_rules["order_mapping"],
        default_loc=updater_rules["default_locations"][context.library].get(
            context.collection
        ),
        collection=context.collection,
        record_type=context.record_type,
    )


def get_message_bus(
    parser: Annotated[Any, Depends(get_parser)],
    matcher: Annotated[Any, Depends(get_matcher)],
    uow: Annotated[Any, Depends(get_uow)],
    updater: Annotated[Any, Depends(get_updater)],
    storage: Annotated[Any, Depends(local_file_storage)],
):
    """Instantiates the bus and registers all command/event handlers."""
    return bootstrap_message_bus(
        uow=uow, storage=storage, parser=parser, matcher=matcher, updater=updater
    )


def get_process_manager(
    bus: Annotated[Any, Depends(get_message_bus)], uow: Annotated[Any, Depends(get_uow)]
) -> process_manager.WorkflowManager:
    """Provides the Process Manager to the FastAPI endpoints."""
    return process_manager.WorkflowManager(bus=bus, uow=uow)
