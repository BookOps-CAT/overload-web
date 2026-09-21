"""API router for Overload Web Worldcat2Sierra."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from overload_web.application.wc2s import match
from overload_web.presentation import deps

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/match_record", response_class=HTMLResponse)
def match_record(
    request: Request,
    # file: Annotated[list, Depends(deps.load_wc2s_file)],
    # criteria: Annotated[Any, Depends(deps.UserCriteria.from_form)],
    marc_parser: Annotated[Any, Depends(deps.get_marc_parser)],
    source_data: Annotated[Any, Depends(deps.source_data_from_load)],
    oclc_handler: Annotated[Any, Depends(deps.oclc_fetcher)],
) -> HTMLResponse:
    out = match.MatchWorldcat2Sierra.execute(
        fetcher=oclc_handler,
        source_data=[i.model_dump() for i in source_data],
        parser=marc_parser,
    )
    out_dict = {}
    for item in out:
        out_dict[item.source_data.id] = [
            i.full_record for i in item.full_record_matches
        ]
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="wc2s_partials/wc2s_results.html",
        context={"wc2s_results": out, "out_dict": out_dict},
    )
