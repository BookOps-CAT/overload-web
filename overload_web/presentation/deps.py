import logging
import os
from contextlib import asynccontextmanager
from inspect import Parameter, Signature
from typing import Annotated, AsyncGenerator, TypeVar

from fastapi import APIRouter, Form, UploadFile
from sqlmodel import SQLModel, create_engine
from starlette.datastructures import UploadFile as StarlettUploadFile

from overload_web.application import file_service
from overload_web.files.infrastructure import file_models, sftp
from overload_web.presentation import schemas

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=schemas.BaseModelAlias)


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


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: APIRouter) -> AsyncGenerator[None, None]:
    logger.info("Starting up Overload...")
    create_db_and_tables()
    yield
    logger.info("Shutting down Overload...")


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
        service = file_service.FileTransferService(
            loader=sftp.SFTPFileLoader.create_loader_for_vendor(vendor)
        )
        loaded_files = [
            service.loader.load(name=f, dir=vendor_dir) for f in remote_files
        ]
        file_list.extend(
            [file_models.VendorFileModel(**f.__dict__) for f in loaded_files]
        )
    return file_list


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
