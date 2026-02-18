"""HTMX router for UI fragments. Serves HTML partials in response to HTMX requests."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])


@htmx_router.get("/forms/vendor-files", response_class=HTMLResponse)
def get_vendor_file_form(request: Request, file_source: str) -> HTMLResponse:
    """Renders form for remote file upload."""
    if file_source == "remote":
        return request.app.state.templates.TemplateResponse(
            request=request, name="forms/remote_files.html"
        )
    else:
        return request.app.state.templates.TemplateResponse(
            request=request, name="forms/local_files.html"
        )


@htmx_router.get("/forms/context", response_class=HTMLResponse)
def get_context_form(request: Request) -> HTMLResponse:
    """Renders form for context input."""
    return request.app.state.templates.TemplateResponse(
        request=request, name="forms/context.html"
    )


@htmx_router.get("/forms/disabled-context", response_class=HTMLResponse)
def get_disabled_context_form(
    request: Request, library: str, collection: str, record_type: str
) -> HTMLResponse:
    """Renders disabled context input form with selected values."""
    context = {"library": library, "collection": collection, "record_type": record_type}
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/disabled_context.html",
        context={"context": context},
    )


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
            context={"disabled": False},
        )

    return request.app.state.templates.TemplateResponse(
        name="forms/collection_field.html",
        request=request,
        context={"disabled": True},
    )
