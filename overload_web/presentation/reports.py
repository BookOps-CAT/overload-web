"""API router for Overload Web backend services related to reporting"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from overload_web.application.pvf.report_service import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.presentation import pvf_deps

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/summary", response_class=HTMLResponse)
def get_output_report(
    request: Request,
    batch_id: str,
    record_type: str,
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
) -> HTMLResponse:
    """
    Create a report for a workflow based on processing statistics.

    This report is used on the report summary page after pvf workflow.

    Args:
        batch_id: the id for the batch of processed files and their statistics
        record_type: the workflow used in the process (eg. "acq", "cat", or "sel").
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.

    Returns:
        the report data wrapped in a `HTMLResponse` object

    """
    out = CreatePVFOutputReport.execute(
        batch_id=batch_id, uow=uow, record_type=record_type
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/summary.html", context=out
    )


@api_router.get("/detailed", response_class=HTMLResponse)
def get_detailed_report(
    request: Request, batch_id: str, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> HTMLResponse:
    """
    Retrieve processing statistics and return a detailed report for a workflow.

    This report is used on the report details page after pvf workflow.

    Args:
        batch_id: the id for the batch of processed files and their statistics
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.

    Returns:
        the report data wrapped in a `HTMLResponse` object

    """
    out = GetDetailedReportData.execute(batch_id=batch_id, uow=uow)
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"detailed_report": out}
    )


@api_router.post("/write", response_class=HTMLResponse)
def save_processing_statistics(
    request: Request,
    batch_id: str,
    record_type: str,
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    writer: Annotated[Any, Depends(pvf_deps.get_report_writer)],
) -> HTMLResponse:
    """
    Save all processing statistics for a workflow to a google sheet.

    Args:
        batch_id: the id for the batch of processed files and their statistics
        record_type: the workflow used in the process (eg. "acq", "cat", or "sel").
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
        writer: a `ports.ReportWriter` object to interact with the Google Sheets API

    Returns:
        Whether or not the report data was successfully written wrapped
        in a `HTMLResponse` object.

    """
    WriteOutputReport.execute(
        batch_id=batch_id, uow=uow, writer=writer, record_type=record_type
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"written_report": True}
    )
