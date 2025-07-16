"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from overload_web import constants
from overload_web.application import services
from overload_web.domain import models
from overload_web.infrastructure import factories
from overload_web.presentation import depends_funcs, schemas

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api", tags=["api"])
templates = Jinja2Templates(directory="overload_web/presentation/templates")


@api_router.get("/")
def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        JSON response indicating the application is active.
    """
    return JSONResponse(content={"app": "Overload Web"})


@api_router.get("/forms/context", response_class=HTMLResponse)
def get_context_form(
    request: Request,
    context: Annotated[
        dict[str, str | dict], Depends(depends_funcs.get_context_form_fields)
    ],
) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="context/form.html",
        context={"context_form_fields": context},
    )


@api_router.get("/forms/template", response_class=HTMLResponse)
def get_template_form(request: Request) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="vendor_templates/template.html",
        context={"field_constants": constants.FIELD_CONSTANTS},
    )


@api_router.get("/list-remote-files", response_class=HTMLResponse)
def list_remote_files(request: Request, vendor: str) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server

    Args:
        vendor: the vendor whose server should be accessed

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    service = factories.create_remote_file_service(vendor)
    files = service.loader.list(dir=os.environ[f"{vendor.upper()}_SRC"])
    return templates.TemplateResponse(
        request=request,
        name="files/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/process-vendor-file", response_class=HTMLResponse)
def process_vendor_file(
    request: Request,
    record_type: Annotated[models.bibs.RecordType, Form(...)],
    library: Annotated[models.bibs.LibrarySystem, Form(...)],
    collection: Annotated[models.bibs.Collection, Form(...)],
    files: Annotated[
        list[schemas.VendorFileModel], Depends(depends_funcs.normalize_files)
    ],
    template_input: Annotated[
        schemas.TemplateModel, Depends(schemas.TemplateModel.from_form_data)
    ],
):
    service = services.records.RecordProcessingService(
        library=library, collection=collection, record_type=record_type
    )
    template_data = {k: v for k, v in template_input.model_dump().items() if v}
    context_dict = {
        "record_type": record_type,
        "library": library,
        "collection": collection,
        "template_data": template_data,
    }
    out_files = []
    for n, file in enumerate(files):
        bibs = service.parse(data=file.content)
        processed_bibs = service.process_records(
            records=bibs, template_data=template_data
        )
        marc_binary = service.write_marc_binary(records=processed_bibs)
        out_files.append(
            {
                f"file_{n}": {
                    "name": file.file_name,
                    "binary_content": marc_binary.read()[0:10],
                    "bibs": [
                        {"domain_bib": i.domain_bib.__dict__, "bib": str(i.bib)}
                        for i in processed_bibs
                    ],
                }
            }
        )
    context_dict["files"] = out_files
    return templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context=context_dict
    )


@api_router.post("/write-local")
def write_local_file(
    vendor_file: schemas.VendorFileModel,
    dir: str,
) -> JSONResponse:
    """Write a file to a local directory."""
    service = factories.create_local_file_service()
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/write-remote")
def write_remote_file(
    vendor_file: schemas.VendorFileModel,
    dir: str,
    vendor: str,
) -> JSONResponse:
    """Write a file to a remote directory."""
    service = factories.create_remote_file_service(vendor=vendor)
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )
