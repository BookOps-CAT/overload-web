"""HTMX router for Overload Web UI fragments.

Serves HTML partials in response to HTMX requests.
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import constants
from overload_web.infrastructure import factories
from overload_web.presentation import depends_funcs, schemas

htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])
templates = Jinja2Templates(directory="overload_web/presentation/templates")


@htmx_router.get("/context-form", response_class=HTMLResponse)
def get_context_form(
    request: Request,
    context: Annotated[
        dict[str, str | dict], Depends(depends_funcs.get_context_form_fields)
    ],
):
    return templates.TemplateResponse(
        "context/form.html",
        {
            "request": request,
            "context_form_fields": context,
        },
    )


@htmx_router.get("/template-input", response_class=HTMLResponse)
def get_template_input(request: Request):
    return templates.TemplateResponse(
        "partials/template.html",
        {"request": request, "field_constants": constants.FIELD_CONSTANTS},
    )


@htmx_router.get("/file-source", response_class=HTMLResponse)
def get_file_source(request: Request):
    return templates.TemplateResponse("files/file_source.html", {"request": request})


@htmx_router.get("/upload-form", response_class=HTMLResponse)
def get_local_upload_form(request: Request):
    return templates.TemplateResponse(
        "partials/file_upload_form.html", {"request": request}
    )


@htmx_router.get("/remote-file-form", response_class=HTMLResponse)
def get_remote_file_form(request: Request):
    return templates.TemplateResponse(
        "partials/remote_file_form.html",
        {"request": request, "vendors": constants.VENDORS},
    )


@htmx_router.get("/list-remote-files", response_class=HTMLResponse)
def list_remote_files(request: Request, vendor: str):
    service = factories.create_remote_file_service(vendor)
    files = service.loader.list(dir=os.environ[f"{vendor.upper()}_SRC"])
    return templates.TemplateResponse(
        "partials/remote_file_list.html",
        {
            "request": request,
            "files": files,
            "vendor": vendor,
            "directory": os.environ[f"{vendor.upper()}_SRC"],
        },
    )


@htmx_router.post("/load-remote-files", response_class=HTMLResponse)
def load_remote_files(
    request: Request,
    file: list[str] = Form(...),
    vendor: str = Form(...),
):
    vendor_dir = os.environ[f"{vendor.upper()}_SRC"]
    service = factories.create_remote_file_service(vendor)
    files = [service.loader.load(name=f, dir=vendor_dir) for f in file]
    models = [schemas.VendorFileModel(**f.__dict__) for f in files]
    return templates.TemplateResponse(
        "partials/loaded_files_summary.html",
        {
            "request": request,
            "files": models,
        },
    )


@htmx_router.get("/pvf-button", response_class=HTMLResponse)
def get_pvf_button(request: Request):
    return templates.TemplateResponse(
        "partials/pvf_button.html",
        {"request": request},
    )
