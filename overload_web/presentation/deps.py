"""Dependency injection functions."""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, Generator

from fastapi import Depends, Form
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.commands.file_io import LoadAllWorkflowFiles
from overload_web.infrastructure import (
    batch_db,
    clients,
    file_io,
    marc_engine,
    reporter,
    template_db,
)
from overload_web.presentation import schemas

logger = logging.getLogger(__name__)


def get_engine_with_uri():
    """Get the Postgres database URI from environment variables."""
    db_type = os.environ.get("DB_TYPE", "sqlite")
    user = os.environ.get("POSTGRES_USER")
    pw = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    name = os.environ.get("POSTGRES_DB")
    uri = f"{db_type}://{user}:{pw}@{host}:{port}/{name}"
    uri = uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")
    engine = create_engine(uri)
    return engine


def create_db_and_tables(engine) -> None:
    """Create the database and tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


def get_session(
    engine: Any = Depends(get_engine_with_uri),
) -> Generator[Session, None, None]:
    """Create a new database session with and `engine` injected via Depends.

    FastAPI will treat `engine` as a dependency instead of a required
    request parameter, avoiding 422 validation errors on endpoints
    that depend on this session provider.
    """
    with Session(engine) as session:
        yield session


def order_template_db(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[template_db.OrderTemplateRepository, None, None]:
    """Create an order template repository."""
    yield template_db.OrderTemplateRepository(session=session)


def pvf_batch_db(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[batch_db.PVFBatchRepository, None, None]:
    """Create an PVFBatch repository."""
    yield batch_db.PVFBatchRepository(session=session)


def incoming_file_db(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[file_io.IncomingFileRepository, None, None]:
    """Create an PVFBatch repository."""
    yield file_io.IncomingFileRepository(session=session)


def local_file_storage() -> file_io.LocalFileStorage:
    return file_io.LocalFileStorage()


def remote_file_loader(vendor: str) -> Generator[file_io.SFTPFileLoader, None, None]:
    """Create an SFTP file loader service."""
    yield file_io.SFTPFileLoader.create_loader_for_vendor(vendor=vendor)


def get_fetcher(
    library: Annotated[str, Form(...)],
) -> Generator[clients.SierraBibFetcher, None, None]:
    """Create a Sierra bib fetcher service for a library."""
    yield clients.FetcherFactory().make(library)


def get_marc_engine(
    context: Annotated[
        schemas.ProcessingContext, Depends(schemas.ProcessingContext.from_form)
    ],
) -> Generator[marc_engine.MarcEngine, None, None]:
    """Create a `MarcEngine` service with injected dependencies."""
    with open("overload_web/data/mapping_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    config = marc_engine.MarcEngineConfig(
        marc_order_mapping=constants["marc_order_mapping"],
        default_loc=constants["default_locations"][context.library].get(
            context.collection
        ),
        bib_id_tag=constants["bib_id_tag"][context.library],
        library=context.library,
        record_type=context.record_type,
        collection=context.collection,
        parser_bib_mapping=constants["bib_domain_mapping"],
        parser_order_mapping=constants["order_domain_mapping"],
        parser_vendor_mapping=constants["vendor_info_options"][context.library],
    )
    yield marc_engine.MarcEngine(rules=config)


def get_report_handler() -> reporter.PandasReportHandler:
    """Return a `PandasReportHandler` in order to generate reports."""
    return reporter.PandasReportHandler()


def get_report_writer() -> reporter.GoogleSheetsReporter:
    """Return a `GoogleSheetsReporter` in order to write stats to a Google Sheet."""
    return reporter.GoogleSheetsReporter()


def load_files(
    workflow_id: str = Form(...), repo: Any = Depends(incoming_file_db)
) -> list:
    return LoadAllWorkflowFiles.execute(
        workflow_id=workflow_id, storage=file_io.LocalFileStorage(), repo=repo
    )
