"""Frontend router used to generate pages using `Jinja2` templates.

Serves HTML pages for Overload Web's user interface.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

logger = logging.getLogger(__name__)
frontend_router = APIRouter(tags=["frontend"])


@frontend_router.get("/", response_class=HTMLResponse)
def root(request: Request, page_title: str = "Overload Web") -> HTMLResponse:
    """
    Renders the home page.

    Args:
        request: `FastAPI` request object.
        page_title: optional title to override the default.

    Returns:
        HTML response for the home page.
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

    Args:
        request: `FastAPI` request object.
        page_title: optional title to override the default.

    Returns:
        HTML response for the home page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request, name="context_form.html", context={"page_title": page_title}
    )


@frontend_router.post("/process", response_class=HTMLResponse)
def post_context_form(
    record_type: str = Form(...), library: str = Form(...), collection: str = Form(...)
) -> RedirectResponse:
    """
    Takes input from form in `context_form.html` and redirects to appropriate
    endpoint for file processing. All args are passed to endpoint via an html form.

    Args:
        record_type:
            the type of record to be processed as a str
        library:
            the library whose records are to be processed as a str
        collection:
            the collection whose records are to be processed as a str

    Returns:
        `RedirectResponse` to appropriate endpoint for record type
    """
    return RedirectResponse(
        url=f"/process/{record_type}?library={library}&collection={collection}",
        status_code=303,
    )


@frontend_router.get("/process/acq", response_class=HTMLResponse)
def process_acq_records_page(
    request: Request,
    library: str,
    collection: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the 'Process Vendor File' page for the Acquisitions workflow.

    Args:
        request:
            `FastAPI` request object.
        library:
            the library whose records are to be processed as a str
        collection:
            the collection whose records are to be processed as a str
        page_title:
            optional title to override the default.

    Returns:
        HTML response for the vendor file page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="process_order_records.html",
        context={
            "library": library,
            "collection": collection,
            "record_type": "acq",
            "page_title": page_title,
        },
    )


@frontend_router.get("/process/cat", response_class=HTMLResponse)
def process_cat_records_page(
    request: Request,
    library: str,
    collection: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the 'Process Vendor File' page for the Cataloging workflow.

    Args:
        request:
            `FastAPI` request object.
        library:
            the library whose records are to be processed as a str
        collection:
            the collection whose records are to be processed as a str
        page_title:
            optional title to override the default.

    Returns:
        HTML response for the vendor file page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="process_full_records.html",
        context={
            "library": library,
            "collection": collection,
            "record_type": "cat",
            "page_title": page_title,
        },
    )


@frontend_router.get("/process/sel", response_class=HTMLResponse)
def process_sel_records_page(
    request: Request,
    library: str,
    collection: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the 'Process Vendor File' page for the Selection workflow.

    Args:
        request:
            `FastAPI` request object.
        library:
            the library whose records are to be processed as a str
        collection:
            the collection whose records are to be processed as a str
        page_title:
            optional title to override the default.

    Returns:
        HTML response for the vendor file page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="process_order_records.html",
        context={
            "library": library,
            "collection": collection,
            "record_type": "sel",
            "page_title": page_title,
        },
    )
