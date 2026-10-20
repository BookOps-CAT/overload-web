"""Dependency injection functions."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlmodel import SQLModel, create_engine

from overload_web.bootstrap import bootstrap_message_bus
from overload_web.domain.pvf import services
from overload_web.infrastructure import (
    file_io,
    marc_handler,
    reporter,
    sierra_clients,
    unit_of_work,
)

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
def get_parser_rules() -> dict[str, Any]:
    """Open and cache parsing rules"""
    with open("overload_web/data/parsing_rules.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache
def get_updater_rules() -> dict[str, Any]:
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


def get_message_bus(
    uow: Annotated[Any, Depends(get_uow)],
    storage: Annotated[Any, Depends(local_file_storage)],
):
    """Instantiates the bus and registers all command/event handlers."""
    parser_rules = get_parser_rules()
    updater_rules = get_updater_rules()
    return bootstrap_message_bus(
        uow=uow,
        storage=storage,
        parser=services.BibParser(
            handler=marc_handler.MarcParser(),
            bib_mapping=parser_rules["bib_mapping"],
            order_mapping=parser_rules["order_mapping"],
            vendor_mapping=parser_rules["vendor_mapping"],
        ),
        matcher=services.BibMatcher(fetcher_factory=sierra_clients.FetcherFactory.make),
        updater=services.BibUpdater(
            handler=marc_handler.MarcUpdater(),
            bib_id_tags=updater_rules["bib_id_tag"],
            order_mapping=updater_rules["order_mapping"],
            default_locations=updater_rules["default_locations"],
        ),
    )
