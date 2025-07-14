"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
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


@api_router.post("/process/{record_type}")
def process_vendor_file(
    record_type: models.bibs.RecordType,
    context: schemas.ContextModel,
    records: list[schemas.VendorFileModel],
    template_data: Optional[schemas.TemplateModel] = None,
) -> StreamingResponse:
    """
    Process a list of `VendorFileModel` objects.

    Args:
        record_type:
            the type of records being processed as an enum (either 'full' or 'order-level')
        context:
            session-specific contextual data including library, collection, and vendor
        records:
            a list of files to be process as `VendorFileModel` objects
        template_data:
            optional data to be used to update order records

    Returns:
        The processed files as a `StreamingResponse`

    """
    service: (
        services.records.FullRecordProcessingService
        | services.records.OrderRecordProcessingService
    )
    session_context = models.context.SessionContext(
        library=context.library, collection=context.collection, vendor=context.vendor
    )
    if str(record_type) == "full":
        service = services.records.FullRecordProcessingService(context=session_context)
    else:
        template = template_data.__dict__
        matchpoints = [i for i in list(template["matchpoints"].__dict__.values()) if i]
        template["matchpoints"] = matchpoints
        service = services.records.OrderRecordProcessingService(
            context=session_context, template=template
        )
    bibs = service.parse(data=records[0].content)
    processed_bibs = service.process_records(records=bibs)
    marc_binary = service.write_marc_binary(records=processed_bibs)
    return StreamingResponse(
        marc_binary,
        media_type="application/marc",
        headers={
            "Content-Disposition": f"attachment; filename={records[0].file_name}_out.mrc"
        },
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
