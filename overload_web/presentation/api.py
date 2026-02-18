"""API router for Overload Web backend services."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from overload_web.application.commands import (
    CreateFullRecordsProcessingReport,
    CreateOrderRecordsProcessingReport,
    CreateOrderTemplate,
    GetOrderTemplate,
    ListOrderTemplates,
    ListVendorFiles,
    ProcessFullRecords,
    ProcessOrderRecords,
    UpdateOrderTemplate,
    WriteFile,
)
from overload_web.presentation import deps, dto

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: APIRouter) -> AsyncGenerator[None, None]:
    """Create and drop database tables on startup/shutdown."""
    logger.info("Starting up Overload...")
    engine = deps.get_engine_with_uri()
    deps.create_db_and_tables(engine)
    yield
    logger.info("Shutting down Overload...")
    engine.dispose()


api_router = APIRouter(prefix="/api", tags=["api"], lifespan=lifespan)


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[Any, Depends(dto.from_form(dto.TemplateCreateModel))],
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Save a new order template to the template database.

    Args:
        template: the order template as an `TemplateCreateModel` object.
        repository: a `repository.SqlModelRepository` object

    Returns:
        the saved order template wrapped in a `HTMLResponse` object
    """
    saved_template = CreateOrderTemplate.execute(obj=template, repository=repository)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/order_template.html",
        context={"template": saved_template.__dict__},
    )


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request,
    template_id: str,
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Retrieve an order template from the database.

    Args:
        template_id: the template's ID as a string.
        repository: a `repository.SqlModelRepository` object

    Returns:
        the retrieved order template wrapped in a `HTMLResponse` object
    """
    template = GetOrderTemplate.execute(template_id=template_id, repository=repository)
    template_out = {k: v for k, v in template.__dict__.items() if v} if template else {}
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="order_templates/rendered.html",
        context={"template": template_out},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request,
    repository: Annotated[Any, Depends(deps.order_template_db)],
    offset: int = 0,
    limit: int = 20,
) -> HTMLResponse:
    """
    List order templates in the database.

    Args:
        repository: a `repository.SqlModelRepository` object
        offset: the first template to be listed
        limit: the maximum number of templates to list

    Returns:
        a list of order templates retrieved from the database wrapped in a
        `HTMLResponse` object
    """
    template_list = ListOrderTemplates.execute(
        repository=repository, offset=offset, limit=limit
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="order_templates/template_list.html",
        context={"templates": template_list},
    )


@api_router.patch("/template", response_class=HTMLResponse)
def update_template(
    request: Request,
    template_id: Annotated[str, Form(...)],
    template_patch: Annotated[Any, Depends(dto.from_form(dto.TemplatePatchModel))],
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Apply patch updates to an order templates in the database.

    Args:
        repository:
            a `repository.SqlModelRepository` object
        template_id:
            the template's ID as a string.
        template_patch:
            data to be updated in the template as an `TemplatePatchModel` object

    Returns:
        the updated order template wrapped in a `HTMLResponse` object
    """
    updated_template = UpdateOrderTemplate.execute(
        repository=repository, template_id=template_id, obj=template_patch
    )
    template_out = (
        {k: v for k, v in updated_template.__dict__.items() if v}
        if updated_template
        else {}
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/order_template.html",
        context={"template": template_out},
    )


@api_router.post("/local-file")
def write_local_file(
    vendor_file: dto.VendorFileModel,
    dir: str,
    writer: Annotated[Any, Depends(deps.local_file_writer)],
) -> JSONResponse:
    """Write a file to a local directory."""
    out_files = WriteFile.execute(file=vendor_file, dir=dir, writer=writer)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.get("/remote-files", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    vendor: str,
    loader: Annotated[Any, Depends(deps.remote_file_loader)],
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server.

    Args:
        vendor: the vendor whose server to access

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    files = ListVendorFiles.execute(
        dir=os.environ[f"{vendor.upper()}_SRC"], loader=loader
    )
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
    writer: Annotated[Any, Depends(deps.remote_file_writer)],
) -> JSONResponse:
    """Write a file to a remote directory."""
    out_files = WriteFile.execute(file=vendor_file, dir=dir, writer=writer)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/full-records/process-vendor-file", response_class=HTMLResponse)
def process_full_records(
    request: Request,
    service_handler: Annotated[Any, Depends(deps.get_pvf_handler)],
    files: Annotated[list[dto.VendorFileModel], Depends(deps.normalize_files)],
    report_handler: Annotated[Any, Depends(deps.get_report_handler)],
) -> HTMLResponse:
    """
    Process one or more files of MARC records.

    Uses a `ProcessingHandler` to process MARC records.

    Args:
        service_handler:
            a `ProcessingHandler` object created using library, collection,
            and record_type args
        files:
            a list of vendor files from a local upload or a vendor's SFTP as
            `VendorFileModel` objects.

    Returns:
        the processed files and report data wrapped in a `HTMLResponse` object

    """
    out_files = []
    for file in files:
        out_file = ProcessFullRecords.execute(
            data=file.content, handler=service_handler, file_name=file.file_name
        )
        out_files.append(out_file)
    report = CreateFullRecordsProcessingReport.execute(
        out_files, handler=report_handler
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={
            "report": report_handler.summary_report_output(
                report.summary,
                classes=["table"],
            ),
            "detailed_report": report_handler.report_to_html(
                report.detailed_data, classes=["table"]
            ),
        },
    )


@api_router.post("/order-records/process-vendor-file", response_class=HTMLResponse)
def process_order_records(
    request: Request,
    service_handler: Annotated[Any, Depends(deps.get_pvf_handler)],
    files: Annotated[list[dto.VendorFileModel], Depends(deps.normalize_files)],
    order_template: Annotated[Any, Depends(dto.from_form(dto.TemplateDataModel))],
    matchpoints: Annotated[Any, Depends(dto.from_form(dto.MatchpointSchema))],
    report_handler: Annotated[Any, Depends(deps.get_report_handler)],
) -> HTMLResponse:
    """
    Process one or more files of MARC records.

    Uses a `ProcessingHandler` to process MARC records.

    Args:
        service_handler:
            an `ProcessingHandler` created using library, collection,
            and record_type args.
        files:
            a list of vendor files from a local upload or a vendor's SFTP as
            `VendorFileModel` objects.
        order_template:
            an order template loaded from the database or input via an html form.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.
        reporter:
            A `ports.ReportHandler` object

    Returns:
        the processed files and report data wrapped in a `HTMLResponse` object

    """
    out_files = []
    for file in files:
        out_file = ProcessOrderRecords.execute(
            data=file.content,
            handler=service_handler,
            template_data=order_template.model_dump(),
            matchpoints=matchpoints.model_dump(),
            file_name=file.file_name,
        )
        out_files.append(out_file)
    report = CreateOrderRecordsProcessingReport.execute(
        out_files, handler=report_handler
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={
            "report": report_handler.summary_report_output(
                report.summary,
                classes=["table"],
            ),
            "detailed_report": report_handler.report_to_html(
                report.detailed_data, classes=["table"]
            ),
        },
    )
