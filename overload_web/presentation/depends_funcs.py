import json
import os
from typing import Annotated, Optional, Union

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
    vendor: Annotated[Optional[str], Form(...)] = None,
) -> list[schemas.VendorFileModel]:
    if source == "remote":
        if not vendor:
            raise ValueError("Vendor must be provided for remote files")
        vendor_dir = os.environ[f"{vendor.upper()}_SRC"]
        service = factories.create_remote_file_service(vendor)
        loaded_files = [service.loader.load(name=f, dir=vendor_dir) for f in files]
        return [schemas.VendorFileModel(**f.__dict__) for f in loaded_files]
    else:
        file_models = [
            schemas.VendorFileModel.create(file_name=f.filename, content=f.file.read())
            for f in files
        ]
        return file_models
