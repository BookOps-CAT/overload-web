import json
import logging
import os
from functools import lru_cache
from inspect import Parameter, Signature
from typing import Annotated, Generator, TypeVar

from fastapi import Depends, Form, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine
from starlette.datastructures import UploadFile as StarlettUploadFile

from overload_web import config
from overload_web.application import file_service, record_service
from overload_web.infrastructure import schemas

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


@lru_cache
def load_constants() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


uri = config.get_postgres_uri()
engine = create_engine(uri)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def normalize_files(
    files: Annotated[list[UploadFile] | list[str], Form(...)],
    vendor: Annotated[str, Form(...)],
) -> list[schemas.VendorFileModel]:
    remote_files = []
    local_files = []
    for file in files:
        if isinstance(file, StarlettUploadFile):
            local_files.append(file)
        else:
            remote_files.append(file)

    file_models = []
    if local_files:
        file_models.extend(
            [
                schemas.VendorFileModel.create(
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
        file_models.extend(
            [schemas.VendorFileModel(**f.__dict__) for f in loaded_files]
        )
    return file_models


def get_record_service(
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
