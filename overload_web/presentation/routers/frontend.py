"""Frontend router used to generate pages using `Jinja2` templates.

Serves HTML pages for Overload Web's user interface.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from overload_web.presentation import schemas

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
    in order to determine the correct processing workflow.

    Args:
        request: `FastAPI` Request object.
        page_title: optional title to override the default.

    Returns:
        HTML template response for the 'Process Vendor File' page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request, name="pvf_home.html", context={"page_title": page_title}
    )


@frontend_router.post("/process", response_class=HTMLResponse)
def post_context_form(
    processing_context: schemas.ProcessingContext = Form(),
) -> RedirectResponse:
    """
    Takes input from form in `pvf_home.html` and redirects to appropriate
    endpoint for file processing. All args are passed to endpoint via an html form.

    Args:
        processing_context:
            A `ProcessingContext` model created from a form.

            This model contains:

                library:
                    the library whose records are to be processed as a str
                collection:
                    the collection whose records are to be processed as a str
                record_type:
                    the type of record to be processed as a str

    Returns:
        `RedirectResponse` to the appropriate endpoint based on processing context.
    """
    return RedirectResponse(
        url=f"/process/{processing_context.record_type}?library={processing_context.library}&collection={processing_context.collection}",
        status_code=303,
    )


@frontend_router.get("/process/{record_type}", response_class=HTMLResponse)
def process_records_page(
    request: Request,
    library: str,
    collection: str,
    record_type: str,
    page_title: str = "Process Vendor File",
) -> HTMLResponse:
    """
    Renders the 'Process Vendor File' page based for workflow.

    Takes values passed via a form to the `ProcessingContext` model and renders
    the appropriate page. The component parts of this page are determined by htmx
    partials that are rendered based on form inputs.

    Args:
        request:
            `FastAPI` Request object.
        library:
            the library whose records are to be processed as a str.
        collection:
            the collection whose records are to be processed as a str.
        record_type:
            the type of record being processed as a str.
        page_title:
            optional title to override the default.

    Returns:
        HTML response for the vendor file page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="process_records.html",
        context={
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "page_title": page_title,
        },
    )


@frontend_router.get("/forms/update-context", response_class=HTMLResponse)
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
