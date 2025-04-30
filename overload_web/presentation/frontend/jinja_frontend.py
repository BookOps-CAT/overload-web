"""Frontend router using `Jinja2` templates.

Serves HTML pages for Overload Web's user interface.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import constants

frontend_router = APIRouter()
templates = Jinja2Templates(directory="overload_web/presentation/frontend/templates")

CONTEXT: Dict[str, Any] = {
    "application": constants.APPLICATION,
    "field_constants": constants.FIELD_CONSTANTS,
}


@frontend_router.get("/", response_class=HTMLResponse)
def root(request: Request, page_title: str = "Overload Web") -> HTMLResponse:
    """
    Renders the home page with default context.

    Args:
        request: `FastAPI` request object.
        page_title: optional title to override the default.

    Returns:
        HTML response for the home page.
    """
    CONTEXT["page_title"] = page_title
    return templates.TemplateResponse(
        request=request, name="home.html", context=CONTEXT
    )


@frontend_router.get("/vendor_file", response_class=HTMLResponse)
def vendor_file_page(
    request: Request, page_title: str = "Process Vendor File"
) -> HTMLResponse:
    """
    Renders the vendor file processing page.

    Args:
        request: `FastAPI` request object.
        page_title: optional title for the page.

    Returns:
        HTML response for the vendor file page.
    """
    CONTEXT["page_title"] = page_title
    return templates.TemplateResponse(request=request, name="pvf.html", context=CONTEXT)
