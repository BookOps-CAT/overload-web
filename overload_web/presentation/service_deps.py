import json
import logging
import os
from functools import lru_cache
from typing import Annotated, Any, Generator

from fastapi import Depends, Form
from sqlmodel import Session, create_engine

from overload_web.application import file_service, record_service, template_service
from overload_web.files.infrastructure import local_io, sftp
from overload_web.order_templates.infrastructure import repository

logger = logging.getLogger(__name__)


@lru_cache
def load_constants() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


def get_postgres_uri() -> str:
    db_type = os.environ.get("DB_TYPE", "sqlite")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    password = os.environ.get("POSTGRES_PASSWORD")
    user = os.environ.get("POSTGRES_USER")
    db_name = os.environ.get("POSTGRES_DB")
    uri = f"{db_type}://{user}:{password}@{host}:{port}/{db_name}"
    return uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")


engine = create_engine(get_postgres_uri())


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def record_processing_service(
    record_type: Annotated[str, Form(...)],
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    yield record_service.RecordProcessingService(
        library=library, collection=collection, record_type=record_type, rules=constants
    )


def local_file_writer() -> Generator[file_service.FileWriterService, None, None]:
    yield file_service.FileWriterService(writer=local_io.LocalFileWriter())


def remote_file_loader(
    vendor: str,
) -> Generator[file_service.FileTransferService, None, None]:
    yield file_service.FileTransferService(
        loader=sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor)
    )


def remote_file_writer(
    vendor: str,
) -> Generator[file_service.FileWriterService, None, None]:
    yield file_service.FileWriterService(
        writer=sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor)
    )


def template_handler(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[template_service.OrderTemplateService, None, None]:
    yield template_service.OrderTemplateService(
        repo=repository.SqlModelRepository(session=session)
    )
