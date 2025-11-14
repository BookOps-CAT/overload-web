import json
import logging
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from inspect import Parameter, Signature
from typing import Annotated, Any, AsyncGenerator, Generator, TypeVar

from fastapi import APIRouter, Depends, Form, UploadFile
from sqlmodel import Session, SQLModel, create_engine
from starlette.datastructures import UploadFile as StarlettUploadFile

from overload_web.application import file_service, record_service, template_service
from overload_web.files.infrastructure import file_models
from overload_web.presentation import config, schemas

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=schemas.BaseModelAlias)


@lru_cache
def load_constants() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


engine = create_engine(config.get_postgres_uri())


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: APIRouter) -> AsyncGenerator[None, None]:
    logger.info("Starting up Overload...")
    create_db_and_tables()
    yield
    logger.info("Shutting down Overload...")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def normalize_files(
    files: Annotated[list[UploadFile] | list[str], Form(...)],
    vendor: Annotated[str, Form(...)],
) -> list[file_models.VendorFileModel]:
    remote_files = []
    local_files = []
    for file in files:
        if isinstance(file, StarlettUploadFile):
            local_files.append(file)
        else:
            remote_files.append(file)

    file_list = []
    if local_files:
        file_list.extend(
            [
                file_models.VendorFileModel.create(
                    file_name=f.filename, content=f.file.read()
                )
                for f in local_files
            ]
        )
    if remote_files and vendor:
        vendor_dir = os.environ[f"{vendor.upper()}_SRC"]
        service = file_service.FileTransferService.create_remote_file_service(vendor)
        loaded_files = [
            service.loader.load(name=f, dir=vendor_dir) for f in remote_files
        ]
        file_list.extend(
            [file_models.VendorFileModel(**f.__dict__) for f in loaded_files]
        )
    return file_list


def record_processing_service(
    record_type: Annotated[str, Form(...)],
    library: Annotated[str, Form(...)],
    collection: Annotated[str, Form(...)],
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> Generator[record_service.RecordProcessingService, None, None]:
    yield record_service.RecordProcessingService(
        library=library, collection=collection, record_type=record_type, rules=constants
    )


def from_form(model_class: type[T]):
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


def local_file_handler() -> Generator[file_service.FileTransferService, None, None]:
    yield file_service.FileTransferService.create_local_file_service()


def remote_file_handler(
    vendor: str,
) -> Generator[file_service.FileTransferService, None, None]:
    yield file_service.FileTransferService.create_remote_file_service(vendor=vendor)


def template_handler(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[template_service.OrderTemplateService, None, None]:
    yield template_service.OrderTemplateService(session=session)
