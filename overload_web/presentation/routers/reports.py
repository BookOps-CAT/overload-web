"""API router for Overload Web backend services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.application.commands.reporting import (
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
    handler: Annotated[Any, Depends(deps.get_report_handler)],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
) -> HTMLResponse:
    out = CreatePVFOutputReport.execute(
        batch_id=batch_id, handler=handler, repo=repository, record_type=record_type
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/summary.html", context=out
    )


@api_router.get("/detailed", response_class=HTMLResponse)
def get_detailed_report(
    request: Request,
    batch_id: str,
    handler: Annotated[Any, Depends(deps.get_report_handler)],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
) -> HTMLResponse:
    out = GetDetailedReportData.execute(
        batch_id=batch_id, handler=handler, repo=repository
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"detailed_report": out}
    )


@api_router.post("/write", response_class=HTMLResponse)
def write_report_to_google_sheet(
    request: Request,
    id: str,
    record_type: Annotated[str, Form()],
    handler: Annotated[Any, Depends(deps.get_report_handler)],
    repository: Annotated[Any, Depends(deps.pvf_batch_db)],
    writer: Annotated[Any, Depends(deps.get_report_writer)],
) -> HTMLResponse:
    out = WriteOutputReport.execute(
        batch_id=id,
        handler=handler,
        repo=repository,
        writer=writer,
        record_type=record_type,
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"detailed_report": out}
    )
