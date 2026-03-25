"""API router for Overload Web backend services."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from overload_web.application.commands.file_io import ListVendorFiles
from overload_web.application.commands.order_template import (
    CreateOrderTemplate,
    GetOrderTemplate,
    ListOrderTemplates,
    UpdateOrderTemplate,
)
from overload_web.application.commands.process import (
    CombineMarcFiles,
    ProcessFullRecords,
    ProcessOrderRecords,
)
from overload_web.application.commands.statistics import (
    CreateFullRecordsProcessingReport,
    CreateOrderRecordsProcessingReport,
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
        repository: a `repository.OrderTemplateRepository` object

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
        repository: a `repository.OrderTemplateRepository` object

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
        repository: a `repository.OrderTemplateRepository` object
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
            a `repository.OrderTemplateRepository` object
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


@api_router.post("/full-records/process-vendor-file", response_class=HTMLResponse)
def process_full_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    local_files: Annotated[list[UploadFile] | None, Form()] = None,
    remote_file_names: Annotated[list[str] | None, Form()] = None,
    vendor: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Process one or more files of full-level MARC records.

    Args:
        marc_engine:
            a `ports.MarcEnginePort` object used by the command.
        fetcher:
            a `ports.BibFetcher` object used by the command.
        local_files:
            a list of files from a local upload as `VendorFileModel` objects.
        remote_files:
            a list of vendor files from a vendor's SFTP as `VendorFileModel` objects.
        vendor:
            the vendor whose files are being processed as a string.
    Returns:
        the processed files and report data wrapped in a `HTMLResponse` object

    """
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    combined = CombineMarcFiles.execute(
        data=[i.content for i in all_files], marc_engine=marc_engine
    )
    processed = ProcessFullRecords.execute(
        data=combined, marc_engine=marc_engine, fetcher=fetcher
    )
    report = CreateFullRecordsProcessingReport.execute(
        processed, file_names=[i.file_name for i in all_files]
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"report": report.__dict__},
    )


@api_router.post("/order-records/process-vendor-file", response_class=HTMLResponse)
def process_order_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    order_template: Annotated[Any, Depends(dto.from_form(dto.TemplateDataModel))],
    matchpoints: Annotated[Any, Depends(dto.from_form(dto.MatchpointSchema))],
    local_files: Annotated[list[UploadFile] | None, Form()] = None,
    remote_file_names: Annotated[list[str] | None, Form()] = None,
    vendor: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Process one or more files of order-level MARC records.

    Args:
        marc_engine:
            a `ports.MarcEnginePort` object used by the command.
        fetcher:
            a `ports.BibFetcher` object used by the command.
        local_files:
            a list of files from a local upload as `VendorFileModel` objects.
        remote_files:
            a list of vendor files from a vendor's SFTP as `VendorFileModel` objects.
        order_template:
            an order template loaded from the database or input via an html form.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.

    Returns:
        the processed files and report data wrapped in a `HTMLResponse` object

    """
    out_files = []
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    for file in all_files:
        out_file = ProcessOrderRecords.execute(
            data=file.content,
            marc_engine=marc_engine,
            fetcher=fetcher,
            template_data=order_template.model_dump(),
            matchpoints=matchpoints.model_dump(),
            file_name=file.file_name,
        )
        out_files.append(out_file)
    report = CreateOrderRecordsProcessingReport.execute(out_files)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"report": report.__dict__},
    )
