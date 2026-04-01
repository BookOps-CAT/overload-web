"""HTMX router for UI fragments. Serves HTML partials in response to HTMX requests."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])


@htmx_router.get("/forms/templates", response_class=HTMLResponse)
def get_template_form(request: Request) -> HTMLResponse:
    """Renders form for creating/editing order templates."""
    return request.app.state.templates.TemplateResponse(
        request=request, name="forms/template_form.html"
    )


@htmx_router.get("/forms/update-context", response_class=HTMLResponse)
def get_updated_context_form(
    request: Request,
    library: str | None = None,
    record_type: str | None = None,
    collection: str | None = None,
):

    ctx = {
        "library": library,
        "record_type": record_type,
        "collection": collection,
        "disabled": False,
    }
    if library == "bpl":
        ctx["disabled"] = True
        return request.app.state.templates.TemplateResponse(
            name="forms/updated_context.html", request=request, context=ctx
        )
    return request.app.state.templates.TemplateResponse(
        name="forms/updated_context.html", request=request, context=ctx
    )
