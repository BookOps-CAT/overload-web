"""Dependency injection functions."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Form, Request, UploadFile
from sqlmodel import SQLModel, create_engine

from overload_web.domain.pvf import bib_services, match_service
from overload_web.infrastructure import (
    file_io,
    marc_handler,
    oclc,
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


def get_marc_parser() -> marc_handler.MarcParser:
    """Create a `MarcParser` service with injected dependencies."""
    return marc_handler.MarcParser()


def oclc_fetcher(
    user_criteria: Annotated[
        schemas.UserCriteria, Depends(schemas.UserCriteria.from_form)
    ],
) -> oclc.WorldcatFetcher:
    return oclc.WorldcatFetcher(session=oclc.OclcSession(library=user_criteria.library))


def load_wc2s_file(file: UploadFile) -> list[str]:
    lines = file.file.readlines()
    return [i.decode("utf-8").strip("\r\n") for i in lines]


def source_data_from_load(
    ids: Annotated[list[str], Depends(load_wc2s_file)],
    data: Annotated[schemas.UserCriteria, Depends(schemas.UserCriteria.from_form)],
) -> list:
    return [
        schemas.SourceDataModel(
            id=i,
            id_type=data.id_type,
            library=data.library,
            collection=data.collection,
            material_type=data.material_type,
            action=data.action,
            record_level=data.record_level,
            required_cataloging_agency=data.cat_agency,
            required_cataloging_rules=data.cat_rules,
        )
        for i in ids
    ]


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


def get_matcher(fetcher: Any = Depends(get_fetcher)) -> match_service.BibMatcher:
    """Create a BibMatcher service for a library."""
    return match_service.BibMatcher(fetcher=fetcher)


def get_parser(
    context: Annotated[
        schemas.ProcessingContext, Depends(schemas.ProcessingContext.from_form)
    ],
    parser_rules: Annotated[dict[str, Any], Depends(parser_rules)],
) -> bib_services.BibParser:
    """Create a BibParser service for a library."""
    parser = marc_handler.MarcParser()
    return bib_services.BibParser(
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
) -> bib_services.BibUpdater:
    """Create a BibUpdater service for a library."""
    updater = marc_handler.MarcUpdater()
    return bib_services.BibUpdater(
        handler=updater,
        bib_id_tag=updater_rules["bib_id_tag"][context.library],
        library=context.library,
        order_mapping=updater_rules["order_mapping"],
        default_loc=updater_rules["default_locations"][context.library].get(
            context.collection
        ),
        record_type=context.record_type,
    )
