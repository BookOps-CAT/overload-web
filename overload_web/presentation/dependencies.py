import json
import os
from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Depends, Form, UploadFile
from sqlmodel import Session, SQLModel, create_engine

from overload_web import config
from overload_web.application import services
from overload_web.presentation import schemas


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


def get_context_form_fields(
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> dict[str, dict]:
    field_list = constants["context_form"]
    return {i: constants[i] for i in field_list}


def get_marc_rules(
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> dict[str, dict]:
    return constants["marc_mapping"]


def get_template_form_fields(
    constants: Annotated[dict[str, dict], Depends(load_constants)],
) -> dict[str, dict]:
    fixed_field_list = constants["template_fixed_fields"]
    var_field_list = constants["template_var_fields"]
    matchpoints = constants["matchpoints"]
    fixed_fields = {i: constants[i] for i in fixed_field_list}
    var_fields = {i: constants[i] for i in var_field_list}
    matchpoint_fields = {
        i: {
            "label": f"{i.split('_')[0].title()}",
            "options": constants["matchpoint_options"],
        }
        for i in matchpoints
    }
    return {
        "fixed_fields": fixed_fields,
        "var_fields": var_fields,
        "matchpoints": matchpoint_fields,
        "bib_formats": constants["material_form"],
    }


def normalize_files(
    source: Annotated[str, Form(...)],
    files: Annotated[list[UploadFile] | list[str], Form(...)],
    vendor: Annotated[str, Form(...)],
) -> list[schemas.VendorFileModel]:
    if source == "remote" and not vendor:
        raise ValueError("Vendor must be provided for remote files")

    file_models = []

    remote_files = []
    local_files = []
    for file in files:
        if isinstance(file, UploadFile):
            local_files.append(file)
        else:
            remote_files.append(file)

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
        service = services.file.FileTransferService.create_remote_file_service(vendor)
        loaded_files = [
            service.loader.load(name=f, dir=vendor_dir) for f in remote_files
        ]
        file_models.extend(
            [schemas.VendorFileModel(**f.__dict__) for f in loaded_files]
        )
    return file_models
