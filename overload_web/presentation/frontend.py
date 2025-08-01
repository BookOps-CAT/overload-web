"""Frontend router using `Jinja2` templates.

Serves HTML pages for Overload Web's user interface.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from overload_web import config

logger = logging.getLogger(__name__)
frontend_router = APIRouter(tags=["frontend"])
templates = config.get_templates()


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
    return templates.TemplateResponse(
        request=request, name="home.html", context={"page_title": page_title}
    )


@frontend_router.get("/process", response_class=HTMLResponse)
def vendor_file_page(
    request: Request, page_title: str = "Process Vendor File"
) -> HTMLResponse:
    """
    Renders the 'Process Vendor File' page.

    Args:
        request: `FastAPI` request object.
        page_title: optional title to override the default.

    Returns:
        HTML response for the home page.
    """
    return templates.TemplateResponse(
        request=request, name="context_form.html", context={"page_title": page_title}
    )


@frontend_router.post("/process", response_class=HTMLResponse)
def post_context_form(
    record_type: str = Form(...), library: str = Form(...), collection: str = Form(...)
) -> RedirectResponse:
    """
    Takes input from form on `process.html` and redirects to appropriate
    endpoint for file processing.

    Args:
        record_type:
            the type of record to be processed as a str passed to a form
        library:
            the library whose records are to be processed as a str passed to a form
        collection:
            the collection whose records are to be processed as a str passed to a form

    Returns:
        `RedirectResponse` to appropriate endpoint for record type
    """
    return RedirectResponse(
        url=f"/process/context?library={library}&collection={collection}&record_type={record_type}",
        status_code=303,
    )


@frontend_router.get("/process/context", response_class=HTMLResponse)
def process_records_page(
    request: Request,
    library: str,
    collection: str,
    record_type: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the vendor file processing page for full MARC records.

    Args:
        request:
            `FastAPI` request object.
        library:
            the library whose records are to be processed passed from
            `/process` endpoint.
        collection:
            the collection whose records are to be processed passed from
            `/process` endpoint.
        record_type:
            the type of records to be processed (ie. 'order_level' or 'full') passed
            from `/process` endpoint.
        page_title:
            optional title for the page.

    Returns:
        HTML response for the vendor file page.
    """
    return templates.TemplateResponse(
        request=request,
        name="process.html",
        context={
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "page_title": page_title,
        },
    )
