"""HTMX router for Overload Web UI fragments.

Serves HTML partials in response to HTMX requests.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web.presentation import deps

logger = logging.getLogger(__name__)
htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])
templates = Jinja2Templates(directory="overload_web/presentation/templates")

ContextFormDep = Annotated[dict[str, str | dict], Depends(deps.context_form_fields)]
TemplateFormDep = Annotated[dict[str, str | dict], Depends(deps.template_form_fields)]


@htmx_router.get("/forms/local-files", response_class=HTMLResponse)
def get_local_upload_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="files/local_form.html")


@htmx_router.get("/forms/remote-files", response_class=HTMLResponse)
def get_remote_file_form(
    request: Request,
    fields: Annotated[dict[str, str | dict], Depends(deps.load_constants)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="files/remote_form.html",
        context={"vendors": fields["vendors"]},
    )


@htmx_router.get("/forms/context", response_class=HTMLResponse)
def get_context_form(request: Request, form_fields: ContextFormDep) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="context/form.html",
        context={"context_form_fields": form_fields},
    )


@htmx_router.get("/forms/disabled-context", response_class=HTMLResponse)
def get_disabled_context_form(
    request: Request,
    fields: ContextFormDep,
    library: str,
    collection: str,
    record_type: str,
) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="context/disabled_form.html",
        context={
            "context_form_fields": fields,
            "context": {
                "library": library,
                "collection": collection,
                "record_type": record_type,
            },
        },
    )


@htmx_router.get("/forms/templates", response_class=HTMLResponse)
def get_template_form(request: Request, fields: TemplateFormDep) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"field_constants": fields, "template": {}},
    )
