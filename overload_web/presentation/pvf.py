"""API router for Overload Web backend MARC file processing services."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.application.pvf.process_manager import FullLevelWorkflowManager
from overload_web.domain.pvf import models
from overload_web.presentation import pvf_deps, schemas

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/workflow", response_class=HTMLResponse)
def initialize_workflow(
    request: Request, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> HTMLResponse:
    workflow_id = str(uuid.uuid4())
    with uow:
        state = models.WorkflowState(
            id=workflow_id, status=models.WorkflowStatus.PENDING
        )
        uow.workflow_states.save(state)
        uow.commit()
    logger.info(f"Created new workflow ID: {workflow_id}")
    request.app.state.workflow_id = workflow_id
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/context_updates.html",
        context={"workflow_id": workflow_id},
    )


@api_router.post("/process-order-records", response_class=HTMLResponse)
def process_order_records(
    request: Request,
    background_tasks: BackgroundTasks,
    matchpoints: Annotated[Any, Depends(schemas.MatchpointsModel.from_form)],
    order_template: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
    process_manager: Annotated[Any, Depends(pvf_deps.get_process_manager)],
    record_type: Annotated[str, Form(...)],
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
    workflow_id = request.app.state.workflow_id
    background_tasks.add_task(
        process_manager.handle_workflow_started,
        workflow_id=workflow_id,
        vendor=getattr(order_template, "vendor", "UNKNOWN"),
        matchpoints=matchpoints.model_dump(),
        template_data=order_template.model_dump(),
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/polling_indicator.html",
        context={"workflow_id": workflow_id, "record_type": record_type},
    )


@api_router.post("/process-full-records", response_class=HTMLResponse)
def process_full_records(
    request: Request,
    background_tasks: BackgroundTasks,
    matcher: Annotated[Any, Depends(pvf_deps.get_matcher)],
    parser: Annotated[Any, Depends(pvf_deps.get_parser)],
    record_type: Annotated[str, Form(...)],
    storage: Annotated[Any, Depends(pvf_deps.local_file_storage)],
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    updater: Annotated[Any, Depends(pvf_deps.get_updater)],
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
    workflow_id = request.app.state.workflow_id
    background_tasks.add_task(
        FullLevelWorkflowManager.start_full_level_workflow,
        storage=storage,
        workflow_id=workflow_id,
        matcher=matcher,
        updater=updater,
        parser=parser,
        uow=uow,
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/polling_indicator.html",
        context={"workflow_id": workflow_id, "record_type": record_type},
    )


@api_router.get("/workflow/{workflow_id}/status", response_class=HTMLResponse)
def workflow_status_check(
    request: Request, workflow_id: str, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> HTMLResponse:
    """HTMX endpoint to poll workflow progress."""
    with uow:
        state = uow.workflow_states.get(workflow_id)
        logger.info(f"Current workflow state {state.status}")
    if not state:
        return HTMLResponse("<div class='error'>Workflow not found.</div>")
    if state.status == models.WorkflowStatus.COMPLETED:
        # Swap out the polling indicator for the final results
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="pvf_partials/pvf_results.html",
            context={"batch_id": state.batch_id, "record_type": state.record_type},
        )
    elif state.status == models.WorkflowStatus.FAILED:
        return HTMLResponse(f"<div class='error'>Error: {state.error_message}</div>")

    # Still processing, return the polling indicator again
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pvf_partials/polling_indicator.html",
        context={"workflow_id": workflow_id},
    )
