"""API router for Overload Web process vendor file services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.application.commands.process import (
    CombineMarcFiles,
    ProcessFullRecords,
    ProcessOrderRecords,
    SaveProcessedRecords,
)
from overload_web.presentation import deps, dto

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/acq/process-vendor-file", response_class=HTMLResponse)
def process_acq_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    order_template: Annotated[Any, Depends(deps.from_form(dto.TemplateDataModel))],
    matchpoints: Annotated[Any, Depends(deps.from_form(dto.MatchpointSchema))],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    local_files: Annotated[list | None, Form()] = None,
    remote_file_names: Annotated[list | None, Form()] = None,
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
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    template_data = order_template.model_dump()
    matchpoints = matchpoints.model_dump()
    processed = ProcessOrderRecords.execute(
        batches={f"{i.file_name}": i.content for i in all_files},
        marc_engine=marc_engine,
        fetcher=fetcher,
        template_data=template_data,
        matchpoints=matchpoints,
    )
    batch = SaveProcessedRecords.execute(repo=repository, batch=processed)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": batch["id"]},
    )


@api_router.post("/cat/process-vendor-file", response_class=HTMLResponse)
def process_cat_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    local_files: Annotated[list | None, Form()] = None,
    remote_file_names: Annotated[list | None, Form()] = None,
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
        data=combined,
        marc_engine=marc_engine,
        fetcher=fetcher,
        file_names=[i.file_name for i in all_files],
    )
    batch = SaveProcessedRecords.execute(repo=repository, batch=processed)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": batch["id"]},
    )


@api_router.post("/sel/process-vendor-file", response_class=HTMLResponse)
def process_sel_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    order_template: Annotated[Any, Depends(deps.from_form(dto.TemplateDataModel))],
    matchpoints: Annotated[Any, Depends(deps.from_form(dto.MatchpointSchema))],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    local_files: Annotated[list | None, Form()] = None,
    remote_file_names: Annotated[list | None, Form()] = None,
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
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    template_data = order_template.model_dump()
    matchpoints = matchpoints.model_dump()
    processed = ProcessOrderRecords.execute(
        batches={f"{i.file_name}": i.content for i in all_files},
        marc_engine=marc_engine,
        fetcher=fetcher,
        template_data=template_data,
        matchpoints=matchpoints,
    )
    batch = SaveProcessedRecords.execute(repo=repository, batch=processed)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": batch["id"]},
    )
