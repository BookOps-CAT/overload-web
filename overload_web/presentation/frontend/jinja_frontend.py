"""Frontend router using `Jinja2` templates.

Serves HTML pages for Overload Web's user interface.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from overload_web import constants

logger = logging.getLogger(__name__)
frontend_router = APIRouter()
templates = Jinja2Templates(directory="overload_web/presentation/frontend/templates")

CONTEXT: Dict[str, Any] = {
    "application": constants.APPLICATION,
    "field_constants": constants.FIELD_CONSTANTS,
    "context_vals": constants.CONTEXT_VALS,
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


@frontend_router.get("/process", response_class=HTMLResponse)
def vendor_file_page(
    request: Request, page_title: str = "Process Vendor File"
) -> HTMLResponse:
    CONTEXT["page_title"] = page_title
    return templates.TemplateResponse(
        request=request, name="process.html", context=CONTEXT
    )


@frontend_router.post("/process", response_class=HTMLResponse)
def post_context_form(
    record_type: str = Form(...),
    library: str = Form(...),
    collection: str = Form(...),
    vendor: str = Form(...),
) -> RedirectResponse:
    if record_type == "full":
        return RedirectResponse(
            url=f"/process/full?library={library}&collection={collection}&vendor={vendor}",
            status_code=303,
        )
    else:
        return RedirectResponse(
            url=f"/process/order-level?library={library}&collection={collection}&vendor={vendor}",
            status_code=303,
        )


@frontend_router.get("/process/full", response_class=HTMLResponse)
def process_full_records(
    request: Request,
    library: str,
    collection: str,
    vendor: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the vendor file processing page for full MARC records.

    Args:
        request: `FastAPI` request object.
        page_title: optional title for the page.

    Returns:
        HTML response for the vendor file page.
    """
    CONTEXT.update(
        {
            "selected_context": {
                "library": library,
                "collection": collection,
                "vendor": vendor,
                "record_type": "full",
            },
            "page_title": page_title,
        }
    )
    return templates.TemplateResponse(
        request=request, name="process_full.html", context=CONTEXT
    )


@frontend_router.get("/process/order-level", response_class=HTMLResponse)
def process_order_records(
    request: Request,
    library: str,
    collection: str,
    vendor: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the vendor file processing page for order-level MARC records.

    Args:
        request: `FastAPI` request object.
        page_title: optional title for the page.

    Returns:
        HTML response for the vendor file page.
    """
    CONTEXT.update(
        {
            "selected_context": {
                "library": library,
                "collection": collection,
                "vendor": vendor,
                "record_type": "order_level",
            },
            "page_title": page_title,
        }
    )
    return templates.TemplateResponse(
        request=request, name="process_order.html", context=CONTEXT
    )
