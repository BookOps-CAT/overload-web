"""API router for Overload Web backend MARC file processing services."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.domain.pvf import commands, models
from overload_web.presentation import pvf_deps, schemas
from overload_web.presentation.templates import templates
from overload_web.presentation.utils import safe_html

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/workflow", response_class=HTMLResponse)
def initialize_workflow(
    request: Request, bus: Annotated[Any, Depends(pvf_deps.get_message_bus)]
) -> HTMLResponse:
    """Initialize a workflow for processing vendor files."""
    workflow_id = str(uuid.uuid4())
    bus.send(commands.InitializeWorkflow(workflow_id=workflow_id))
    partial = """
    <input value={workflow_id}
       name="workflow_id"
       id="workflow_id"
       form="pvf-form"
       type="hidden">"""
    html_str = safe_html(partial, workflow_id=workflow_id)
    return HTMLResponse(html_str)


@api_router.post("/process-order-records", response_class=HTMLResponse)
def process_order_records(
    background_tasks: BackgroundTasks,
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    context: Annotated[
        schemas.ProcessingContext, Depends(schemas.ProcessingContext.from_form)
    ],
    order_template: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
    workflow_id: Annotated[str, Form(...)],
) -> HTMLResponse:
    """Process one or more files of order-level MARC records using the acq workflow.

    Args:
        background_tasks:
            tasks run after returning the HTML template response
        bus:
            a `ports.MessageBusPort` object used by the workflow
        context:
            a `schemas.ProcessingContext` object containing the library, collection,
            and record_type for the workflow.
        order_template:
            an order template loaded from the database or input via an html form.
        workflow_id:
            the ID for the given workflow.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object

    """
    background_tasks.add_task(
        bus.send,
        commands.StartOrderLevelRecordsWorkflow(
            collection=context.collection,
            library=context.library,
            matchpoints=order_template.matchpoints,
            record_type=context.record_type,
            template_data=order_template.template_data,
            vendor=getattr(order_template, "vendor", "UNKNOWN"),
            workflow_id=workflow_id,
        ),
    )
    partial = """
    <div hx-get="/pvf/workflow/{workflow_id}/status"
        hx-trigger="every 1s"
        hx-swap="outerHTML">
        <span class="spinner"></span> Processing vendor file...
    </div>"""
    html_str = safe_html(partial, workflow_id=workflow_id)
    return HTMLResponse(html_str)


@api_router.post("/process-full-records", response_class=HTMLResponse)
def process_full_records(
    background_tasks: BackgroundTasks,
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    context: Annotated[
        schemas.ProcessingContext, Depends(schemas.ProcessingContext.from_form)
    ],
    workflow_id: Annotated[str, Form(...)],
) -> HTMLResponse:
    """Process one or more files of full-level MARC records using the cat workflow.

    Args:
        background_tasks:
            tasks run after returning the HTML template response
        bus:
            a `ports.MessageBusPort` object used by the workflow
        context:
            a `schemas.ProcessingContext` object containing the library, collection,
            and record_type for the workflow.
        workflow_id:
            the ID for the given workflow.

    Returns:
        the ID for the processed files and stats wrapped in an `HTMLResponse` object

    """
    background_tasks.add_task(
        bus.send,
        commands.StartFullLevelRecordsWorkflow(
            collection=context.collection,
            library=context.library,
            record_type=context.record_type,
            workflow_id=workflow_id,
        ),
    )
    partial = """
    <div hx-get="/pvf/workflow/{workflow_id}/status"
        hx-trigger="every 1s"
        hx-swap="outerHTML">
        <span class="spinner"></span> Processing vendor file...
    </div>"""
    html_str = safe_html(partial, workflow_id=workflow_id)
    return HTMLResponse(html_str)


@api_router.get("/workflow/{workflow_id}/status", response_class=HTMLResponse)
def workflow_status_check(
    request: Request, workflow_id: str, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> HTMLResponse:
    """HTMX endpoint to poll workflow progress."""
    with uow:
        state = uow.workflow_states.get(workflow_id)
    if not state:
        return HTMLResponse("<div class='error'>Workflow not found.</div>")
    if state.status == models.WorkflowStatus.COMPLETED:
        return templates.TemplateResponse(
            request=request,
            name="pvf/partials/results.html",
            context={"batch_id": state.batch_id, "record_type": state.record_type},
        )
    elif state.status == models.WorkflowStatus.FAILED:
        html_str = safe_html(
            "<div class='error'>Error: {error_message}</div>",
            error_message=state.error_message,
        )
        return HTMLResponse(html_str)
    partial = """
    <div hx-get="/pvf/workflow/{workflow_id}/status"
        hx-trigger="every 1s"
        hx-swap="outerHTML">
        <span class="spinner"></span> Processing vendor file...
    </div>"""
    html_str = safe_html(partial, workflow_id=workflow_id)
    return HTMLResponse(html_str)
