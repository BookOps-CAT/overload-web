"""Dependency injection functions."""

import json
import logging
import os
from inspect import Parameter, Signature
from typing import Annotated, Any, BinaryIO, Generator, Protocol, runtime_checkable

from fastapi import Depends, Form
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine

from overload_web.infrastructure import (
    batch_db,
    clients,
    file_io,
    marc_engine,
    reporter,
    template_db,
)
from overload_web.shared import schemas

logger = logging.getLogger(__name__)


class VendorFileModel(BaseModel, schemas._VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""


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
) -> Generator[template_db.OrderTemplateRepository, None, None]:
    """Create an order template repository."""
    yield template_db.OrderTemplateRepository(session=session)


def pvf_batch_db(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[batch_db.PVFBatchRepository, None, None]:
    """Create an PVFBatch repository."""
    yield batch_db.PVFBatchRepository(session=session)


@runtime_checkable
class FileProtocol(Protocol):
    """A protocol representing a FastAPI `UploadFile` object."""

    filename: str | None
    content_type: str
    file: BinaryIO


def remote_file_loader(vendor: str) -> Generator[file_io.SFTPFileLoader, None, None]:
    """Create an SFTP file loader service."""
    yield file_io.SFTPFileLoader.create_loader_for_vendor(vendor=vendor)


def fetch_files(
    local_files: list[FileProtocol] | None = None,
    remote_file_names: list[str] | None = None,
    vendor: str | None = None,
) -> list[VendorFileModel]:
    """Return all files as (filename, bytes)."""
    logger.info(
        "Fetching files to process: local_uploads=%s, remote_files=%s, vendor=%s",
        local_files,
        remote_file_names,
        vendor,
    )
    files: list[VendorFileModel] = []

    # Local files
    if local_files:
        for f in local_files:
            vendor_file = VendorFileModel(
                file_name=str(f.filename), content=f.file.read()
            )
            files.append(vendor_file)

    # Remote files
    if remote_file_names and vendor:
        loader = file_io.SFTPFileLoader.create_loader_for_vendor(vendor)
        vendor_dir = os.environ[f"{vendor.upper()}_SRC"]
        for name in remote_file_names:
            loaded = loader.load(name=name, dir=vendor_dir)
            vendor_file = VendorFileModel(file_name=name, content=loaded)
            files.append(vendor_file)

    return files


def get_marc_engine_config(
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    record_type: Annotated[str, Form(...)],
) -> marc_engine.MarcEngineConfig:
    with open("overload_web/data/mapping_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return marc_engine.MarcEngineConfig(
        marc_order_mapping=constants["marc_order_mapping"],
        default_loc=constants["default_locations"][library].get(collection),
        bib_id_tag=constants["bib_id_tag"][library],
        library=library,
        record_type=record_type,
        collection=collection,
        parser_bib_mapping=constants["bib_domain_mapping"],
        parser_order_mapping=constants["order_domain_mapping"],
        parser_vendor_mapping=constants["vendor_info_options"][library],
    )


def get_fetcher(
    library: Annotated[str, Form(...)],
) -> Generator[clients.SierraBibFetcher, None, None]:
    """Create a Sierra bib fetcher service for a library."""
    yield clients.FetcherFactory().make(library)


def get_marc_engine(
    config: Annotated[marc_engine.MarcEngineConfig, Depends(get_marc_engine_config)],
) -> Generator[marc_engine.MarcEngine, None, None]:
    """Create a record processing service with injected dependencies."""
    yield marc_engine.MarcEngine(rules=config)


def get_report_handler() -> reporter.PandasReportHandler:
    return reporter.PandasReportHandler()


def from_form(model_class: BaseModel):
    """
    A generic function used to create an object from an html form.
    HTML forms can only take data as strings so this class method is
    needed in order to parse the data into the correct types.
    """
    form_fields = []
    for field_name, model_field in model_class.model_fields.items():
        annotation = model_field.annotation
        default = Form(...) if model_field.is_required() else Form(default=None)
        form_fields.append((field_name, annotation, default))

    def func(**data):
        return model_class(**data)

    params = [
        Parameter(
            name,
            Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=annotation,
        )
        for name, annotation, default in form_fields
    ]
    func.__signature__ = Signature(parameters=params)  # type: ignore[attr-defined]
    return func
