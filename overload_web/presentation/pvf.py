"""API router for Overload Web backend MARC file processing services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.application.pvf.process import (
    ProcessFullRecords,
    ProcessOrderLevelRecords,
)
from overload_web.presentation import deps, schemas

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/acq/process-vendor-file", response_class=HTMLResponse)
def process_acq_records(
    request: Request,
    matcher: Annotated[Any, Depends(deps.get_matcher)],
    matchpoints: Annotated[Any, Depends(schemas.MatchpointsModel.from_form)],
    order_template: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
    parser: Annotated[Any, Depends(deps.get_parser)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    uow: Annotated[Any, Depends(deps.get_uow)],
    updater: Annotated[Any, Depends(deps.get_updater)],
    workflow_id: Annotated[str, Form(...)],
) -> HTMLResponse:
    """
    Process one or more files of order-level MARC records using the acq workflow.

    Args:
        fetcher:
            a `ports.BibFetcher` object used by application service.
        order_template:
            an order template loaded from the database or input via an html form.
        marc_updater:
            a `ports.MarcUpdaterPort` object used by application service.
        marc_parser:
            a `ports.MarcParserPort` object used by application service.
        parsing_rules:
            a `marc_updater.MarcParsingRulesModel` object representing cataloging rules.
        update_rules:
            a `marc_updater.MarcUpdateRulesModel` object representing cataloging rules.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.
        repository:
            a `repository.PVFBatchRepository` object where the processed files and
            their associated statistics will be saved.
        files:
            a list of files to be processed.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object
    """
    processed = ProcessOrderLevelRecords.execute(
        storage=storage,
        workflow_id=workflow_id,
        matcher=matcher,
        template_data=order_template.model_dump(),
        matchpoints=matchpoints.model_dump(),
        updater=updater,
        parser=parser,
        uow=uow,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": processed["id"], "record_type": "acq"},
    )


@api_router.post("/cat/process-vendor-file", response_class=HTMLResponse)
def process_cat_records(
    request: Request,
    matcher: Annotated[Any, Depends(deps.get_matcher)],
    parser: Annotated[Any, Depends(deps.get_parser)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    uow: Annotated[Any, Depends(deps.get_uow)],
    updater: Annotated[Any, Depends(deps.get_updater)],
    workflow_id: Annotated[str, Form(...)],
) -> HTMLResponse:
    """
    Process one or more files of full-level MARC records using the cat workflow.

    Args:
        fetcher:
            a `ports.BibFetcher` object used by application service.
        marc_updater:
            a `ports.MarcUpdaterPort` object used by application service.
        marc_parser:
            a `ports.MarcParserPort` object used by application service.
        parsing_rules:
            a `marc_updater.MarcParsingRulesModel` object representing cataloging rules.
        update_rules:
            a `marc_updater.MarcUpdateRulesModel` object representing cataloging rules.
        repository:
            a `repository.PVFBatchRepository` object where the processed files and
            their associated statistics will be saved.
        files:
            a list of files to be processed.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object
    """
    processed = ProcessFullRecords.execute(
        storage=storage,
        workflow_id=workflow_id,
        matcher=matcher,
        updater=updater,
        parser=parser,
        uow=uow,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": processed["id"], "record_type": "cat"},
    )


@api_router.post("/sel/process-vendor-file", response_class=HTMLResponse)
def process_sel_records(
    request: Request,
    matcher: Annotated[Any, Depends(deps.get_matcher)],
    matchpoints: Annotated[Any, Depends(schemas.MatchpointsModel.from_form)],
    order_template: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
    parser: Annotated[Any, Depends(deps.get_parser)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    uow: Annotated[Any, Depends(deps.get_uow)],
    updater: Annotated[Any, Depends(deps.get_updater)],
    workflow_id: Annotated[str, Form(...)],
) -> HTMLResponse:
    """
    Process one or more files of order-level MARC records using the sel workflow.

    Args:
        fetcher:
            a `ports.BibFetcher` object used by application service.
        order_template:
            an order template loaded from the database or input via an html form.
        marc_updater:
            a `ports.MarcUpdaterPort` object used by application service.
        marc_parser:
            a `ports.MarcParserPort` object used by application service.
        parsing_rules:
            a `marc_updater.MarcParsingRulesModel` object representing cataloging rules.
        update_rules:
            a `marc_updater.MarcUpdateRulesModel` object representing cataloging rules.
        matchpoints:
            a list of matchpoints loaded from an order template in the database or
            input via an html form.
        repository:
            a `repository.PVFBatchRepository` object where the processed files and
            their associated statistics will be saved.
        files:
            a list of files to be processed.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object
    """
    processed = ProcessOrderLevelRecords.execute(
        storage=storage,
        workflow_id=workflow_id,
        matcher=matcher,
        template_data=order_template.model_dump(),
        matchpoints=matchpoints.model_dump(),
        updater=updater,
        parser=parser,
        uow=uow,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/pvf_results.html",
        context={"batch_id": processed["id"], "record_type": "sel"},
    )
