"""API router for Overload Web backend services."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from overload_web.presentation.deps import dto, files, records, templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: APIRouter) -> AsyncGenerator[None, None]:
    """Create and drop database tables on startup/shutdown."""
    logger.info("Starting up Overload...")
    engine = templates.get_engine_with_uri()
    templates.create_db_and_tables(engine)
    yield
    logger.info("Shutting down Overload...")
    engine.dispose()


api_router = APIRouter(prefix="/api", tags=["api"], lifespan=lifespan)

TemplateService = Annotated[Any, Depends(templates.template_handler)]


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[Any, Depends(dto.from_form(dto.TemplateCreateModel))],
    service: TemplateService,
) -> HTMLResponse:
    """
    Save a new order template to the template database.

    Args:
        template: the order template as an `TemplateCreateModel` object.
        service: an `OrderTemplateService` object used to interact with the database.

    Returns:
        the saved order template wrapped in a `HTMLResponse` object
    """
    saved_template = service.save_template(obj=template)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"template": saved_template.__dict__},
    )


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request, template_id: str, service: TemplateService
) -> HTMLResponse:
    """
    Retrieve an order template from the database.

    Args:
        template_id: the template's ID as a string.
        service: an `OrderTemplateService` object used to interact with the database.

    Returns:
        the retrieved order template wrapped in a `HTMLResponse` object
    """
    template = service.get_template(template_id=template_id)
    template_out = {k: v for k, v in template.__dict__.items() if v} if template else {}
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/rendered_template.html",
        context={"template": template_out},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request, service: TemplateService, offset: int = 0, limit: int = 20
) -> HTMLResponse:
    """
    List order templates in the database.

    Args:
        service: an `OrderTemplateService` object used to interact with the database.
        offset: the first template to be listed
        limit: the maximum number of templates to list

    Returns:
        a list of order templates retrieved from the database wrapped in a
        `HTMLResponse` object
    """
    template_list = service.list_templates(offset=offset, limit=limit)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/template_list.html",
        context={"templates": template_list},
    )


@api_router.patch("/template", response_class=HTMLResponse)
def update_template(
    request: Request,
    template_id: Annotated[str, Form(...)],
    template_patch: Annotated[Any, Depends(dto.from_form(dto.TemplatePatchModel))],
    service: TemplateService,
) -> HTMLResponse:
    """
    Apply patch updates to an order templates in the database.

    Args:
        template_id:
            the template's ID as a string.
        template_patch:
            data to be updated in the template as an `TemplatePatchModel` object
        service:
            an `OrderTemplateService` object used to interact with the database.

    Returns:
        the updated order template wrapped in a `HTMLResponse` object
    """
    updated_template = service.update_template(
        template_id=template_id, obj=template_patch
    )
    template_out = (
        {k: v for k, v in updated_template.__dict__.items() if v}
        if updated_template
        else {}
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"template": template_out},
    )


@api_router.post("/local-file")
def write_local_file(
    vendor_file: dto.VendorFileModel,
    dir: str,
    service: Annotated[Any, Depends(files.local_file_writer)],
) -> JSONResponse:
    """Write a file to a local directory."""
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.get("/remote-files", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    vendor: str,
    service: Annotated[Any, Depends(files.remote_file_loader)],
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server.

    Args:
        vendor: the vendor whose server to access

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    files = service.loader.list(dir=os.environ[f"{vendor.upper()}_SRC"])
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="files/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/remote-file")
def write_remote_file(
    vendor_file: dto.VendorFileModel,
    dir: str,
    vendor: str,
    service: Annotated[Any, Depends(files.remote_file_writer)],
) -> JSONResponse:
    """Write a file to a remote directory."""
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/full-records/process-vendor-file", response_class=HTMLResponse)
def process_full_records(
    request: Request,
    full_record_service: Annotated[Any, Depends(records.full_level_processing_service)],
    files: Annotated[list[dto.VendorFileModel], Depends(files.normalize_files)],
) -> HTMLResponse:
    """
    Process one or more files of MARC records.

    Uses `FullRecordProcessingService` to process MARC records.

    Args:
        full_record_service:
            a `FullRecordProcessingService` object created using library, collection,
            and record_type args
        files:
            a list of vendor files from a local upload or a vendor's SFTP as
            `VendorFileModel` objects.

    Returns:
        the processed files and report data wrapped in a `HTMLResponse` object

    """
    out_files = {}
    for file in files:
        out_files[file.file_name] = full_record_service.process_vendor_file(
            data=file.content
        )
    return request.app.state.templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context={"files": out_files}
    )


@api_router.post("/order-records/process-vendor-file", response_class=HTMLResponse)
def process_order_records(
    request: Request,
    order_record_service: Annotated[
        Any, Depends(records.order_level_processing_service)
    ],
    files: Annotated[list[dto.VendorFileModel], Depends(files.normalize_files)],
    order_template: Annotated[Any, Depends(dto.from_form(dto.TemplateDataModel))],
    matchpoints: Annotated[Any, Depends(dto.from_form(dto.MatchpointSchema))],
    vendor: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Process one or more files of MARC records.

    Uses an `OrderRecordProcessingService` to process MARC records.

    Args:
        order_record_service:
            an `OrderRecordProcessingService` created using library, collection,
            and record_type args.
        files:
            a list of vendor files from a local upload or a vendor's SFTP as
            `VendorFileModel` objects.
        order_template:
            an order template loaded from the database or input via an html form.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.
        vendor:
            The vendor name as a string.

    Returns:
        the processed files and report data wrapped in a `HTMLResponse` object

    """
    out_files = {}
    for file in files:
        out_files[file.file_name] = order_record_service.process_vendor_file(
            data=file.content,
            template_data=order_template.model_dump(),
            matchpoints=matchpoints.model_dump(),
            vendor=vendor,
        )
    return request.app.state.templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context={"files": out_files}
    )
