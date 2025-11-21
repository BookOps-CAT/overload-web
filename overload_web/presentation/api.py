"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from overload_web.presentation import (
    deps,
    dto,
    file_service_dep,
    record_service_deps,
    template_service_dep,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: APIRouter) -> AsyncGenerator[None, None]:
    logger.info("Starting up Overload...")
    deps.create_db_and_tables()
    yield
    logger.info("Shutting down Overload...")


api_router = APIRouter(prefix="/api", tags=["api"], lifespan=lifespan)

TemplateService = Annotated[Any, Depends(template_service_dep.template_handler)]


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[Any, Depends(deps.from_form(dto.TemplateCreateModel))],
    service: TemplateService,
) -> HTMLResponse:
    """
    Save a new order template to the template DB.

    Args:
        template: the order template to save as an `TemplateCreateModel` object.
        service: an `OrderTemplateService` object used to interact with the DB

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
    Retrieve an order template from the DB.

    Args:
        template_id: the template's ID as a string.
        service: an `OrderTemplateService` object used to interact with the DB

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
    request: Request,
    service: TemplateService,
    offset: int = 0,
    limit: int = 20,
) -> HTMLResponse:
    """
    List order templates in the DB.

    Args:
        service: an `OrderTemplateService` object used to interact with the DB
        offset: the first template to be listed
        limit: the maximum number of templates to list

    Returns:
        a list of order templates retrieved from the db wrapped in a
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
    template_patch: Annotated[Any, Depends(deps.from_form(dto.TemplatePatchModel))],
    service: TemplateService,
) -> HTMLResponse:
    """
    Apply patch updates to an order templates in the DB.

    Args:
        template_id:
            the template's ID as a string.
        template_patch:
            data to be updated in the template as an `TemplatePatchModel` object
        service:
            an `OrderTemplateService` object used to interact with the DB

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
    service: Annotated[Any, Depends(file_service_dep.local_file_writer)],
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
    service: Annotated[Any, Depends(file_service_dep.remote_file_loader)],
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server.

    Args:
        vendor: the vendor whose server should be accessed

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
    service: Annotated[Any, Depends(file_service_dep.remote_file_writer)],
) -> JSONResponse:
    """Write a file to a remote directory."""
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/process-vendor-file", response_class=HTMLResponse)
def process_vendor_file(
    request: Request,
    service: Annotated[Any, Depends(record_service_deps.record_processing_service)],
    files: Annotated[
        list[dto.VendorFileModel], Depends(file_service_dep.normalize_files)
    ],
    order_template: Annotated[Any, Depends(deps.from_form(dto.TemplateDataModel))],
    matchpoints: Annotated[Any, Depends(deps.from_form(dto.MatchpointSchema))],
    record_type: Annotated[str, Form(...)],
) -> HTMLResponse:
    """
    Process one or more MARC files using the `RecordProcessingService`.

    Args:
        service:
            the `RecordProcessingService` created using library, collection,
            and record_type
        files:
            a list of vendor files from a local upload or a vendor's SFTP
        order_template:
            an order template loaded from the DB or created via a form
        matchpoints:
            a list of matchpoints created from a form
        record_type:
            The type of record as an Literal value from bibs.RecordType.

    Returns:
        the processed files wrapped in a `HTMLResponse` object

    """
    out_files = []
    for file in files:
        output = service.process_vendor_file(
            data=file.content,
            template_data=order_template.model_dump(),
            matchpoints=matchpoints.model_dump(),
            record_type=record_type,
        )
        out_files.append({"file_name": file.file_name, "binary_content": output})
    return request.app.state.templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context={"files": out_files}
    )
