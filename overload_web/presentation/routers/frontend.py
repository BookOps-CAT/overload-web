"""Frontend router used to generate pages using `Jinja2` templates.

Serves HTML pages for Overload Web's user interface.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


frontend_router = APIRouter(tags=["frontend"])


@frontend_router.get("/", response_class=HTMLResponse)
def root(request: Request, page_title: str = "Overload Web") -> HTMLResponse:
    """
    Renders the home page.

    Args:
        request: `FastAPI` Request object.
        page_title: optional title to override the default.

    Returns:
        HTML template response for the home page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request, name="home.html", context={"page_title": page_title}
    )


@frontend_router.get("/process", response_class=HTMLResponse)
def vendor_file_page(
    request: Request, page_title: str = "Process Vendor File"
) -> HTMLResponse:
    """
    Renders the 'Process Vendor File' page.

    This is the first page users see after selecting the Process Vendor File tab and
    it is where they  can input values for `library`, `collection`, and `record_type`
    in order to determine the correct processing workflow. This also generates a
    `workflow_id` to be used while uploading and processing files.

    Args:
        request: `FastAPI` Request object.
        page_title: optional title to override the default.

    Returns:
        HTML template response for the 'Process Vendor File' page.
    """
    workflow_id = str(uuid.uuid4())
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="process_records.html",
        context={"page_title": page_title, "workflow_id": workflow_id},
    )


@frontend_router.get("/forms/update-library", response_class=HTMLResponse)
def get_library_context_update(request: Request, library: str):
    ctx = {"library": library, "disabled": False}
    if library == "bpl":
        ctx["disabled"] = True
        return request.app.state.templates.TemplateResponse(
            name="forms/library_context.html", request=request, context=ctx
        )
    return request.app.state.templates.TemplateResponse(
        name="forms/library_context.html", request=request, context=ctx
    )


@frontend_router.get("/forms/update-collection", response_class=HTMLResponse)
def get_collection_context_update(request: Request, collection: str | None):
    return request.app.state.templates.TemplateResponse(
        name="forms/collection_context.html",
        request=request,
        context={"collection": collection},
    )


@frontend_router.get("/forms/update-record-type", response_class=HTMLResponse)
def get_record_type_context_update(request: Request, record_type: str):
    return request.app.state.templates.TemplateResponse(
        name="forms/record_type_context.html",
        request=request,
        context={"record_type": record_type},
    )
