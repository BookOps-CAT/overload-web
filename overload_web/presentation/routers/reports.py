"""API router for Overload Web backend services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from overload_web.application.commands.reporting import (
    ProcessDetailedReportData,
    ProcessReportData,
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
    out = ProcessReportData.execute(
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
    out = ProcessDetailedReportData.execute(
        batch_id=batch_id, handler=handler, repo=repository
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name="reports/detailed.html", context={"detailed_report": out}
    )
