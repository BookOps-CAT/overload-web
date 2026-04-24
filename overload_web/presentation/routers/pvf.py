"""API router for Overload Web backend MARC file processing services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.application.commands.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.presentation import deps, schemas

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/acq/process-vendor-file", response_class=HTMLResponse)
def process_acq_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    order_template: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    matchpoints: Annotated[Any, Depends(schemas.MatchpointsModel.from_form)],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    local_files: Annotated[list | None, Form()] = None,
    remote_file_names: Annotated[list | None, Form()] = None,
    vendor: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Process one or more files of order-level MARC records using the acq workflow.

    Args:
        fetcher:
            a `ports.BibFetcher` object used by application service.
        order_template:
            an order template loaded from the database or input via an html form.
        marc_engine:
            a `ports.MarcEnginePort` object used by application service.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.
        repository:
            a `repository.PVFBatchRepository` object where the processed files and
            their associated statistics will be saved.
        local_files:
            a list of files from a local upload as `UploadFile` objects.
        remote_file_names:
            a list of names of files to be retrieved from a vendor's SFTP as strings.
        vendor:
            the vendor whose remote files are to be retrieved as a str.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object
    """
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    processed = ProcessAcquisitionsRecords.execute(
        batches={f"{i.file_name}": i.content for i in all_files},
        marc_engine=marc_engine,
        fetcher=fetcher,
        template_data=order_template.model_dump(),
        matchpoints=matchpoints.model_dump(),
        repo=repository,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": processed["id"]},
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
    Process one or more files of full-level MARC records using the cat workflow.

    Args:
        fetcher:
            a `ports.BibFetcher` object used by application service.
        marc_engine:
            a `ports.MarcEnginePort` object used by application service.
        repository:
            a `repository.PVFBatchRepository` object where the processed files and
            their associated statistics will be saved.
        local_files:
            a list of files from a local upload as `UploadFile` objects.
        remote_file_names:
            a list of names of files to be retrieved from a vendor's SFTP as strings.
        vendor:
            the vendor whose remote files are to be retrieved as a str.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object
    """
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    processed = ProcessCatalogingRecords.execute(
        batches={f"{i.file_name}": i.content for i in all_files},
        marc_engine=marc_engine,
        fetcher=fetcher,
        repo=repository,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": processed["id"]},
    )


@api_router.post("/sel/process-vendor-file", response_class=HTMLResponse)
def process_sel_records(
    request: Request,
    fetcher: Annotated[Any, Depends(deps.get_fetcher)],
    order_template: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
    marc_engine: Annotated[Any, Depends(deps.get_marc_engine)],
    matchpoints: Annotated[Any, Depends(schemas.MatchpointsModel.from_form)],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    local_files: Annotated[list | None, Form()] = None,
    remote_file_names: Annotated[list | None, Form()] = None,
    vendor: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Process one or more files of order-level MARC records using the sel workflow.

    Args:
        fetcher:
            a `ports.BibFetcher` object used by application service.
        order_template:
            an order template loaded from the database or input via an html form.
        marc_engine:
            a `ports.MarcEnginePort` object used by application service.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.
        repository:
            a `repository.PVFBatchRepository` object where the processed files and
            their associated statistics will be saved.
        local_files:
            a list of files from a local upload as `UploadFile` objects.
        remote_file_names:
            a list of names of files to be retrieved from a vendor's SFTP as strings.
        vendor:
            the vendor whose remote files are to be retrieved as a str.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object
    """
    all_files = deps.fetch_files(
        local_files=local_files, remote_file_names=remote_file_names, vendor=vendor
    )
    processed = ProcessSelectionRecords.execute(
        batches={f"{i.file_name}": i.content for i in all_files},
        marc_engine=marc_engine,
        fetcher=fetcher,
        template_data=order_template.model_dump(),
        matchpoints=matchpoints.model_dump(),
        repo=repository,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": processed["id"]},
    )
