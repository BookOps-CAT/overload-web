import json
import os
from typing import Annotated, Union

from fastapi import Form, UploadFile

from overload_web.infrastructure import factories
from overload_web.presentation import schemas


def get_context_form_fields() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/presentation/templates/context.json", "r") as fh:
        form_fields = json.load(fh)
    return form_fields


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
