import json
import os
from functools import lru_cache
from typing import Annotated, Any, Union

from fastapi import Depends, Form, UploadFile

from overload_web.infrastructure import factories
from overload_web.presentation import schemas


@lru_cache
def load_constants() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/presentation/constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


@lru_cache
def load_form_fields() -> dict[str, list[str]]:
    with open(
        "overload_web/presentation/form_fields.json", "r", encoding="utf-8"
    ) as fh:
        constants = json.load(fh)
    return constants


def get_context_form_fields(
    constants: Annotated[
        dict[str, dict[str, str | dict[str, str]]], Depends(load_constants)
    ],
    field_list: Annotated[dict[str, list[str]], Depends(load_form_fields)],
) -> dict[str, dict[str, str | dict[str, str]]]:
    return {i: constants[i] for i in field_list["context_form"]}


def get_template_form_fields(
    constants: Annotated[
        dict[str, dict[str, str | dict[str, str]]], Depends(load_constants)
    ],
    field_list: Annotated[dict[str, list[str]], Depends(load_form_fields)],
) -> dict[str, Any]:
    fixed_fields = {i: constants[i] for i in field_list["template_fixed_fields"]}
    var_fields = {i: constants[i] for i in field_list["template_var_fields"]}
    matchpoints = {
        i: {"label": f"{i.title()}", "options": constants["matchpoint_options"]}
        for i in field_list["matchpoints"]
    }
    return {
        "fixed_fields": fixed_fields,
        "var_fields": var_fields,
        "matchpoints": matchpoints,
    }


def normalize_files(
    source: Annotated[str, Form(...)],
    files: Annotated[Union[list[UploadFile], list[str]], Form(...)],
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
        service = factories.create_remote_file_service(vendor)
        loaded_files = [
            service.loader.load(name=f, dir=vendor_dir) for f in remote_files
        ]
        file_models.extend(
            [schemas.VendorFileModel(**f.__dict__) for f in loaded_files]
        )
    return file_models
