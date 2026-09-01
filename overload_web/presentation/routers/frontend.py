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

    This is the first page users see after selecting the Process Vendor File app and
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


@frontend_router.get("/update-context", response_class=HTMLResponse)
def get_context_update(
    request: Request,
    workflow: str,
    library: str = "",
    collection: str = "",
    record_type: str = "",
):
    """
    Updates header based on library, collection, record_type, and selected workflow.

    This endpoint adds the library's logo, collection and record_type to identify
    the system being used in the processing workflow. This endpoint also disables the
    "collection" select box if "bpl" is selected as the library.

    Args:
        request:
            `FastAPI` Request object.
        library:
            the library as a string (either `'nypl'` or `'bpl'`).
        collection:
            the collection as a string (either `'BL'`, `'RL'`, or '').
        record_type:
            the record_type as a string (either `'acq'`, `'cat'`, or `'sel'`).

    Returns:
        HTML partial for updated header and select box.
    """
    collection_disabled = library == "bpl"

    template_form_enabled = record_type in ["acq", "sel"]

    if collection_disabled:
        collection = ""

    return request.app.state.templates.TemplateResponse(
        name=f"{workflow}_partials/context_updates.html",
        request=request,
        context={
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "collection_disabled": collection_disabled,
            "template_form_enabled": template_form_enabled,
        },
    )


@frontend_router.get("/wc2sierra", response_class=HTMLResponse)
def wc2sierra_page(
    request: Request, page_title: str = "WorldCat2Sierra"
) -> HTMLResponse:
    """
    Renders the 'WorldCat2Sierra' page.

    This is the first page users see after selecting the WorldCat2Sierra app.

    Args:
        request: `FastAPI` Request object.
        page_title: optional title to override the default.

    Returns:
        HTML template response for the 'Process Vendor File' page.
    """
    return request.app.state.templates.TemplateResponse(
        request=request, name="wc2sierra.html", context={"page_title": page_title}
    )
