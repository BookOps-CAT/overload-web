"""HTMX router for Overload Web UI fragments.

Serves HTML partials in response to HTMX requests.
"""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])


@htmx_router.get("/forms/local-files", response_class=HTMLResponse)
def get_local_upload_form(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request, name="files/local_form.html"
    )


@htmx_router.get("/forms/remote-files", response_class=HTMLResponse)
def get_remote_file_form(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request, name="files/remote_form.html"
    )


@htmx_router.get("/forms/context", response_class=HTMLResponse)
def get_context_form(request: Request) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return request.app.state.templates.TemplateResponse(
        request=request, name="context/form.html"
    )


@htmx_router.get("/forms/disabled-context", response_class=HTMLResponse)
def get_disabled_context_form(
    request: Request, library: str, collection: str, record_type: str
) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    context = {"library": library, "collection": collection, "record_type": record_type}
    return request.app.state.templates.TemplateResponse(
        request=request, name="context/disabled_form.html", context={"context": context}
    )


@htmx_router.get("/forms/templates", response_class=HTMLResponse)
def get_template_form(request: Request) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return request.app.state.templates.TemplateResponse(
        request=request, name="record_templates/template_form.html"
    )
