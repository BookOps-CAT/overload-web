"""HTMX router for Overload Web UI fragments.

Serves HTML partials in response to HTMX requests.
"""

import os
from typing import Any

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import constants
from overload_web.infrastructure import factories
from overload_web.presentation import schemas

htmx_router = APIRouter(prefix="/htmx", tags=["htmx"])
templates = Jinja2Templates(directory="overload_web/presentation/templates")


@htmx_router.get("/context-form", response_class=HTMLResponse)
def get_context_form(request: Request):
    return templates.TemplateResponse(
        "partials/context_form.html",
        {
            "request": request,
            "context_vals": constants.CONTEXT_VALS,
        },
    )


@htmx_router.post("/set-context", response_class=HTMLResponse)
def set_context(
    request: Request,
    record_type: str = Form(...),
    library: str = Form(...),
    collection: str = Form(...),
):
    selected_context = {
        "record_type": record_type,
        "library": library,
        "collection": collection,
    }

    return templates.TemplateResponse(
        "partials/disabled_context_form.html",
        {
            "request": request,
            "selected_context": selected_context,
            "context_vals": constants.CONTEXT_VALS,
            "field_constants": constants.FIELD_CONSTANTS,
        },
    )


@htmx_router.get("/main-form", response_class=HTMLResponse)
def get_main_form(request: Request):
    selected_context: dict[str, Any] = {}
    return templates.TemplateResponse(
        "partials/main_form.html",
        {
            "request": request,
            "field_constants": constants.FIELD_CONSTANTS,
            "selected_context": selected_context,
        },
    )


@htmx_router.get("/file-source-toggle", response_class=HTMLResponse)
def get_file_source_toggle(request: Request):
    return templates.TemplateResponse(
        "partials/file_source_toggle.html", {"request": request}
    )


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
        },
    )


@htmx_router.post("/load-local-files", response_class=HTMLResponse)
def load_local_files(request: Request, file: list[UploadFile] = File(...)):
    models = [
        schemas.VendorFileModel.create(file_name=f.filename, content=f.file.read())
        for f in file
    ]
    return templates.TemplateResponse(
        "partials/loaded_files_summary.html",
        {
            "request": request,
            "files": models,
        },
    )


@htmx_router.post("/load-remote-files", response_class=HTMLResponse)
def load_remote_files(
    request: Request,
    file: list[str] = Query(...),
    dir: str = Query(...),
    vendor: str = Query(...),
):
    service = factories.create_remote_file_service(vendor)
    files = [service.loader.load(name=f, dir=dir) for f in file]
    models = [schemas.VendorFileModel(**f.__dict__) for f in files]
    return templates.TemplateResponse(
        "partials/loaded_files_summary.html",
        {
            "request": request,
            "files": models,
        },
    )


@htmx_router.get("/template-form", response_class=HTMLResponse)
def get_template_form(request: Request):
    return templates.TemplateResponse(
        "partials/template_input_form.html", {"request": request}
    )


@htmx_router.get("/processing-status", response_class=HTMLResponse)
def get_processing_status(request: Request):
    return templates.TemplateResponse(
        "partials/processing_status.html", {"request": request}
    )


@htmx_router.get("/output-options", response_class=HTMLResponse)
def get_output_options(request: Request):
    return templates.TemplateResponse(
        "partials/output_options.html", {"request": request}
    )
