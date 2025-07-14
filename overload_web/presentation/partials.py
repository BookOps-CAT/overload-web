"""HTMX router for Overload Web UI fragments.

Serves HTML partials in response to HTMX requests.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import constants

htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])
templates = Jinja2Templates(directory="overload_web/presentation/templates")


@htmx_router.get("/file-source", response_class=HTMLResponse)
def get_file_source(request: Request):
    return templates.TemplateResponse("files/file_source.html", {"request": request})


@htmx_router.get("/local-file-form", response_class=HTMLResponse)
def get_local_upload_form(request: Request):
    return templates.TemplateResponse("file/local_form.html", {"request": request})


@htmx_router.get("/remote-file-form", response_class=HTMLResponse)
def get_remote_file_form(request: Request):
    return templates.TemplateResponse(
        "partials/remote_form.html",
        {"request": request, "vendors": constants.VENDORS},
    )


@htmx_router.get("/pvf-button", response_class=HTMLResponse)
def get_pvf_button(request: Request):
    return templates.TemplateResponse(
        "partials/pvf_button.html",
        {"request": request},
    )
