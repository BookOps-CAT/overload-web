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
    CONTEXT["page_title"] = page_title
    return templates.TemplateResponse(
        request=request, name="home.html", context=CONTEXT
    )


@frontend_router.get("/vendor_file", response_class=HTMLResponse)
def vendor_file_page(
    request: Request, page_title: str = "Process Vendor File"
) -> HTMLResponse:
    CONTEXT["page_title"] = page_title
    return templates.TemplateResponse(request=request, name="pvf.html", context=CONTEXT)
