"""API router for Overload Web backend services related to reporting"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from overload_web.application.pvf.reporting import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.presentation import deps

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/summary", response_class=HTMLResponse)
def get_output_report(
    request: Request,
    batch_id: str,
    record_type: str,
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
) -> HTMLResponse:
    """Create a dict to be used on the report summary page after pvf workflow."""
    out = CreatePVFOutputReport.execute(
        batch_id=batch_id, repo=repository, record_type=record_type
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/summary.html", context=out
    )


@api_router.get("/detailed", response_class=HTMLResponse)
def get_detailed_report(
    request: Request,
    batch_id: str,
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
) -> HTMLResponse:
    """Create a dict to be used on the detailed report stats page after pvf workflow."""
    out = GetDetailedReportData.execute(batch_id=batch_id, repo=repository)
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"detailed_report": out}
    )


@api_router.post("/write", response_class=HTMLResponse)
def save_processing_statistics(
    request: Request,
    batch_id: str,
    record_type: str,
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    writer: Annotated[Any, Depends(deps.get_report_writer)],
) -> HTMLResponse:
    """Save processing statistics reports (call number and dupes) to a google sheet."""
    WriteOutputReport.execute(
        batch_id=batch_id, repo=repository, writer=writer, record_type=record_type
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"written_report": True}
    )
