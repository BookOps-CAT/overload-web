"""Dependency injection functions."""

import logging
import os
from typing import Annotated, Any, BinaryIO, Generator, Protocol, runtime_checkable

from fastapi import Depends, Form, UploadFile
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application import ports
from overload_web.application.commands import LoadVendorFile
from overload_web.application.services import record_service
from overload_web.infrastructure import (
    clients,
    loader,
    local_io,
    marc_engine,
    reporter,
    repository,
    sftp,
)
from overload_web.presentation import dto

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
    """Create a new database session. `engine` is injected via Depends.

    FastAPI will treat `engine` as a dependency instead of a required
    request parameter, avoiding 422 validation errors on endpoints
    that depend on this session provider.
    """
    with Session(engine) as session:
        yield session


def order_template_db(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[repository.SqlModelRepository, None, None]:
    """Create an order template repository."""
    yield repository.SqlModelRepository(session=session)


@runtime_checkable
class FileProtocol(Protocol):
    """A protocol representing a FastAPI `UploadFile` object."""

    filename: str | None
    content_type: str
    file: BinaryIO


def local_file_writer() -> Generator[local_io.LocalFileWriter, None, None]:
    """Create a local file writer service."""
    yield local_io.LocalFileWriter()


def remote_file_loader(
    vendor: str,
) -> Generator[sftp.SFTPFileLoader, None, None]:
    """Create an SFTP file loader service."""
    yield sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor)


def remote_file_writer(
    vendor: str,
) -> Generator[sftp.SFTPFileWriter, None, None]:
    """Create an SFTP file writer service."""
    yield sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor)


def fetch_files(
    local_files: list[UploadFile] | None = None,
    remote_file_names: list[str] | None = None,
    vendor: str | None = None,
) -> list[dto.VendorFileModel]:
    """Return all files as (filename, bytes)."""
    logger.info(
        "Fetching files to process: local_uploads=%s, remote_files=%s, vendor=%s",
        local_files,
        remote_file_names,
        vendor,
    )
    files: list[dto.VendorFileModel] = []

    # Local files
    if local_files:
        for f in local_files:
            vendor_file = dto.VendorFileModel(
                file_name=str(f.filename), content=f.file.read()
            )
            files.append(vendor_file)

    # Remote files
    if remote_file_names and vendor:
        loader = sftp.SFTPFileLoader.create_loader_for_vendor(vendor)
        vendor_dir = os.environ[f"{vendor.upper()}_SRC"]
        for name in remote_file_names:
            loaded = LoadVendorFile.execute(name=name, dir=vendor_dir, loader=loader)
            vendor_file = dto.VendorFileModel(
                file_name=str(loaded.file_name), content=loaded.content
            )
            files.append(vendor_file)

    return files


def get_marc_engine_config(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    constants: Annotated[dict[str, Any], Depends(loader.load_config)],
    record_type: Annotated[str, Form(...)],
) -> marc_engine.MarcEngineConfig:
    return loader.marc_engine_config_from_constants(
        constants=constants,
        library=library,
        collection=collection,
        record_type=record_type,
    )


def get_fetcher(
    library: Annotated[str, Form(...)],
) -> Generator[ports.BibFetcher, None, None]:
    """Create a Sierra bib fetcher service for a library."""
    yield clients.FetcherFactory().make(library)


def get_pvf_handler(
    fetcher: Annotated[ports.BibFetcher, Depends(get_fetcher)],
    config: Annotated[marc_engine.MarcEngineConfig, Depends(get_marc_engine_config)],
) -> Generator[record_service.ProcessingHandler, None, None]:
    """Create a record processing service with injected dependencies."""
    yield record_service.ProcessingHandler(
        fetcher=fetcher, engine=marc_engine.MarcEngine(rules=config)
    )


def get_report_handler(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> reporter.PandasReportHandler:
    return reporter.PandasReportHandler(
        library=library, collection=collection, record_type=record_type
    )
