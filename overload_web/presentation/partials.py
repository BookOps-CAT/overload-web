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
        request=request, name="forms/order_template.html"
    )


@htmx_router.get("/forms/collection", response_class=HTMLResponse)
def get_collection_field(request: Request, library: str):
    if library == "nypl":
        return request.app.state.templates.TemplateResponse(
            name="forms/collection_field.html",
            request=request,
            context={"disabled": False, "library": library},
        )

    return request.app.state.templates.TemplateResponse(
        name="forms/collection_field.html",
        request=request,
        context={"disabled": True, "library": library},
    )


@htmx_router.get("/forms/update-context", response_class=HTMLResponse)
def get_updated_context_form(
    request: Request, record_type: str | None = None, collection: str | None = None
):
    return request.app.state.templates.TemplateResponse(
        name="forms/updated_context.html",
        request=request,
        context={"record_type": record_type, "collection": collection},
    )
