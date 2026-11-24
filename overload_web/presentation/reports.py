"""API router for Overload Web backend services related to reporting."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from overload_web.application.pvf import queries
from overload_web.application.pvf.report_service import WriteOutputReport
from overload_web.presentation import pvf_deps
from overload_web.presentation.utils import safe_html

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/write", response_class=HTMLResponse)
def save_processing_statistics(
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    workflow_id: str,
    writer: Annotated[Any, Depends(pvf_deps.get_report_writer)],
) -> HTMLResponse:
    """Save all processing statistics for a workflow to a google sheet.

    Args:
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
        workflow_id: the workflow id for the processed files and their statistics
        writer: a `ports.ReportWriter` object to interact with the Google Sheets API

    Returns:
        Whether or not the report data was successfully written wrapped
        in a `HTMLResponse` object.

    """
    report_data = queries.get_processing_report(workflow_id=workflow_id, uow=uow)
    WriteOutputReport.execute(report_data=report_data, writer=writer)
    partial = """
    <span id="save-report-button"
      hx-swap-oob="outerHTML:#save-report-button"
      class="status-banner status-ok">Processing Statistics Saved</span>"""
    html_str = safe_html(partial, workflow_id=workflow_id)
    return HTMLResponse(html_str)
