"""Dependency injection functions."""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, Generator, Literal

from fastapi import Depends, Form
from pydantic import BaseModel, field_validator, model_validator
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

logger = logging.getLogger(__name__)


class MatchpointsModel(BaseModel):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None

    @classmethod
    def from_form(
        self,
        primary_matchpoint: str | None = Form(default=None),
        secondary_matchpoint: str | None = Form(default=None),
        tertiary_matchpoint: str | None = Form(default=None),
    ) -> MatchpointsModel:
        """Class method used to create a `MatchpointsModel` object from an html form"""
        return MatchpointsModel(
            primary_matchpoint=primary_matchpoint,
            secondary_matchpoint=secondary_matchpoint,
            tertiary_matchpoint=tertiary_matchpoint,
        )


class ProcessingContext(BaseModel):
    """A model that represents context necessary to determine processing workflow."""

    collection: Literal["BL", "RL", ""] | None
    library: Literal["nypl", "bpl"]
    record_type: Literal["acq", "cat", "sel"]

    @field_validator("collection", mode="before")
    @classmethod
    def parse_collection(
        cls, value: Literal["BL", "RL"] | None
    ) -> Literal["BL", "RL"] | None:
        """Parses value of `collection` param from html forms."""
        if not value:
            return None
        else:
            return value

    @model_validator(mode="after")
    def validate_values(self) -> ProcessingContext:
        """Ensures `collection` is not passed when processing BPL records."""
        if self.library == "nypl" and not self.collection:
            raise ValueError("Collection is required for NYPL records.")
        elif self.library == "bpl" and self.collection:
            raise ValueError("Collection should be `None` for BPL records.")
        return self

    @classmethod
    def from_form(
        self,
        collection: Literal["BL", "RL", ""] | None = Form(None),
        library: Literal["nypl", "bpl"] = Form(...),
        record_type: Literal["acq", "cat", "sel"] = Form(...),
    ) -> ProcessingContext:
        """Class method used to create a `ProcessingContext` object from an html form"""
        return ProcessingContext(
            collection=collection, library=library, record_type=record_type
        )


class TemplateDataModel(BaseModel):
    """Pydantic model for serializing/deserializing order template data
    when it is used in a processing workflow"""

    acquisition_type: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
    order_code_1: str | None = None
    order_code_2: str | None = None
    order_code_3: str | None = None
    order_code_4: str | None = None
    order_note: str | None = None
    order_type: str | None = None
    receive_action: str | None = None
    selector_note: str | None = None
    vendor_code: str | None = None
    vendor_notes: str | None = None
    vendor_title_no: str | None = None

    @classmethod
    def from_form(
        self,
        acquisition_type: str | None = Form(default=None),
        blanket_po: str | None = Form(default=None),
        claim_code: str | None = Form(default=None),
        country: str | None = Form(default=None),
        format: str | None = Form(default=None),
        internal_note: str | None = Form(default=None),
        lang: str | None = Form(default=None),
        material_form: str | None = Form(default=None),
        order_code_1: str | None = Form(default=None),
        order_code_2: str | None = Form(default=None),
        order_code_3: str | None = Form(default=None),
        order_code_4: str | None = Form(default=None),
        order_note: str | None = Form(default=None),
        order_type: str | None = Form(default=None),
        receive_action: str | None = Form(default=None),
        selector_note: str | None = Form(default=None),
        vendor_code: str | None = Form(default=None),
        vendor_notes: str | None = Form(default=None),
        vendor_title_no: str | None = Form(default=None),
    ) -> TemplateDataModel:
        """Class method used to create a `TemplateDataModel` object from an html form"""
        return TemplateDataModel(
            acquisition_type=acquisition_type,
            blanket_po=blanket_po,
            claim_code=claim_code,
            country=country,
            format=format,
            internal_note=internal_note,
            lang=lang,
            material_form=material_form,
            order_code_1=order_code_1,
            order_code_2=order_code_2,
            order_code_3=order_code_3,
            order_code_4=order_code_4,
            order_note=order_note,
            order_type=order_type,
            receive_action=receive_action,
            selector_note=selector_note,
            vendor_code=vendor_code,
            vendor_notes=vendor_notes,
            vendor_title_no=vendor_title_no,
        )


class TemplatePatchModel(BaseModel):
    """
    Pydantic model for serializing/deserializing data used to update
    an order template in the database.
    """

    acquisition_type: str | None = None
    agent: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
    name: str | None = None
    order_code_1: str | None = None
    order_code_2: str | None = None
    order_code_3: str | None = None
    order_code_4: str | None = None
    order_note: str | None = None
    order_type: str | None = None
    receive_action: str | None = None
    selector_note: str | None = None
    vendor_code: str | None = None
    vendor_notes: str | None = None
    vendor_title_no: str | None = None

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None

    @classmethod
    def from_form(
        self,
        acquisition_type: str | None = Form(default=None),
        agent: str | None = Form(default=None),
        blanket_po: str | None = Form(default=None),
        claim_code: str | None = Form(default=None),
        country: str | None = Form(default=None),
        format: str | None = Form(default=None),
        internal_note: str | None = Form(default=None),
        lang: str | None = Form(default=None),
        material_form: str | None = Form(default=None),
        name: str | None = Form(default=None),
        order_code_1: str | None = Form(default=None),
        order_code_2: str | None = Form(default=None),
        order_code_3: str | None = Form(default=None),
        order_code_4: str | None = Form(default=None),
        order_note: str | None = Form(default=None),
        order_type: str | None = Form(default=None),
        receive_action: str | None = Form(default=None),
        selector_note: str | None = Form(default=None),
        vendor_code: str | None = Form(default=None),
        vendor_notes: str | None = Form(default=None),
        vendor_title_no: str | None = Form(default=None),
        primary_matchpoint: str | None = Form(default=None),
        secondary_matchpoint: str | None = Form(default=None),
        tertiary_matchpoint: str | None = Form(default=None),
    ) -> TemplatePatchModel:
        """Class model used to create a `TemplatePatchModel` from an html form."""
        return TemplatePatchModel(
            acquisition_type=acquisition_type,
            agent=agent,
            blanket_po=blanket_po,
            claim_code=claim_code,
            country=country,
            format=format,
            internal_note=internal_note,
            lang=lang,
            material_form=material_form,
            name=name,
            order_code_1=order_code_1,
            order_code_2=order_code_2,
            order_code_3=order_code_3,
            order_code_4=order_code_4,
            order_note=order_note,
            order_type=order_type,
            receive_action=receive_action,
            selector_note=selector_note,
            vendor_code=vendor_code,
            vendor_notes=vendor_notes,
            vendor_title_no=vendor_title_no,
            primary_matchpoint=primary_matchpoint,
            secondary_matchpoint=secondary_matchpoint,
            tertiary_matchpoint=tertiary_matchpoint,
        )


class TemplateCreateModel(TemplatePatchModel):
    """
    Pydantic model for serializing/deserializing data used to create
    an order template in the database.

    Inherits `from_from` class method from `TemplatePatchModel` parent class
    which is used when creating a new order template from an html form.
    """

    name: str
    agent: str
    primary_matchpoint: str


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
    context: Annotated[ProcessingContext, Depends(ProcessingContext.from_form)],
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
