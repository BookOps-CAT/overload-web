"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Generator

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, SQLModel, create_engine

from overload_web import config
from overload_web.application import services
from overload_web.domain import models
from overload_web.infrastructure import db, factories
from overload_web.presentation import dependencies, schemas

logger = logging.getLogger(__name__)

uri = config.get_postgres_uri()
engine = create_engine(uri)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
ContextFormFieldsDep = Annotated[
    dict[str, str | dict], Depends(dependencies.get_context_form_fields)
]
TemplateFormFieldsDep = Annotated[
    dict[str, str | dict], Depends(dependencies.get_template_form_fields)
]

api_router = APIRouter(prefix="/api", tags=["api"])
templates = Jinja2Templates(directory="overload_web/presentation/templates")


@api_router.on_event("startup")
def startup_event():
    create_db_and_tables()


@api_router.get("/")
def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        JSON response indicating the application is active.
    """
    return JSONResponse(content={"app": "Overload Web"})


@api_router.get("/forms/context", response_class=HTMLResponse)
def get_context_form(
    request: Request,
    form_fields: ContextFormFieldsDep,
) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="context/form.html",
        context={"context_form_fields": form_fields},
    )


@api_router.get("/forms/disabled-context", response_class=HTMLResponse)
def get_disabled_context_form(
    request: Request,
    fields: ContextFormFieldsDep,
    library: str,
    collection: str,
    record_type: str,
) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="context/disabled_form.html",
        context={
            "context_form_fields": fields,
            "context": {
                "library": library,
                "collection": collection,
                "record_type": record_type,
            },
        },
    )


@api_router.get("/forms/templates", response_class=HTMLResponse)
def template_form(
    request: Request,
    fields: TemplateFormFieldsDep,
) -> HTMLResponse:
    """Get options for template inputs from application constants."""
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"field_constants": fields, "template": {}},
    )


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[
        db.tables.TemplateCreate,
        Depends(db.tables.TemplateCreate.from_form),
        Form(),
    ],
    session: SessionDep,
    fields: TemplateFormFieldsDep,
) -> HTMLResponse:
    new_template = {}
    valid_template = db.tables.Template.model_validate(template)
    service = services.template.TemplateService(session=session)
    saved_template = service.save_template(obj=valid_template)
    new_template.update(saved_template.model_dump())
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"new_template": new_template, "field_constants": fields},
    )


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request,
    template_id: str,
    session: SessionDep,
    fields: TemplateFormFieldsDep,
) -> HTMLResponse:
    template_out = {}
    service = services.template.TemplateService(session=session)
    template = service.get_template(template_id=template_id)
    if template:
        template_out.update({k: v for k, v in template.model_dump().items() if v})
    return templates.TemplateResponse(
        request=request,
        name="record_templates/rendered_template.html",
        context={"template": template_out, "field_constants": fields},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request, session: SessionDep, offset: int = 0, limit: int = 20
) -> HTMLResponse:
    service = services.template.TemplateService(session=session)
    template_list = service.list_templates(offset=offset, limit=limit)
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_list.html",
        context={"templates": [i.model_dump() for i in template_list]},
    )


# @api_router.patch("/templates/{template_id}", response_class=HTMLResponse)
# def update_template(
#     request: Request,
#     template_id: str,
#     template: db.models.TemplateUpdate,
#     uow: UOWDep,
# ) -> HTMLResponse:
#     service = services.template.TemplateService(uow=uow)
#     updated_template = service.save_template(obj=template)
#     return templates.TemplateResponse(
#         request=request,
#         name="record_templates/update_template.html",
#         context={"updated_template": updated_template},
#     )


@api_router.get("/list-remote-files", response_class=HTMLResponse)
def list_remote_files(request: Request, vendor: str) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server

    Args:
        vendor: the vendor whose server should be accessed

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    service = factories.create_remote_file_service(vendor)
    files = service.loader.list(dir=os.environ[f"{vendor.upper()}_SRC"])
    return templates.TemplateResponse(
        request=request,
        name="files/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/process-vendor-file", response_class=HTMLResponse)
def process_vendor_file(
    request: Request,
    record_type: Annotated[models.bibs.RecordType, Form(...)],
    library: Annotated[models.bibs.LibrarySystem, Form(...)],
    collection: Annotated[models.bibs.Collection, Form(...)],
    files: Annotated[
        list[schemas.VendorFileModel], Depends(dependencies.normalize_files)
    ],
    template_input: Annotated[
        schemas.TemplateModel, Depends(schemas.TemplateModel.from_form_data)
    ],
    marc_rules: Annotated[
        dict[str, dict[str, str]], Depends(dependencies.get_marc_rules)
    ],
):
    service = services.records.RecordProcessingService(
        library=library,
        collection=collection,
        record_type=record_type,
        marc_rules=marc_rules,
    )
    template_data = {k: v for k, v in template_input.model_dump().items() if v}
    context_dict = {
        "record_type": record_type,
        "library": library,
        "collection": collection,
        "template_data": template_data,
    }
    out_files = []
    for n, file in enumerate(files):
        bibs = service.parse(data=file.content)
        processed_bibs = service.process_records(
            records=bibs, template_data=template_data
        )
        marc_binary = service.write_marc_binary(records=processed_bibs)
        out_files.append(
            {
                f"file_{n}": {
                    "name": file.file_name,
                    "binary_content": marc_binary.read()[0:10],
                    "bibs": [
                        {"domain_bib": i.domain_bib.__dict__, "bib": str(i.bib)}
                        for i in processed_bibs
                    ],
                }
            }
        )
    context_dict["files"] = out_files
    return templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context=context_dict
    )


@api_router.post("/write-local")
def write_local_file(
    vendor_file: schemas.VendorFileModel,
    dir: str,
) -> JSONResponse:
    """Write a file to a local directory."""
    service = factories.create_local_file_service()
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/write-remote")
def write_remote_file(
    vendor_file: schemas.VendorFileModel,
    dir: str,
    vendor: str,
) -> JSONResponse:
    """Write a file to a remote directory."""
    service = factories.create_remote_file_service(vendor=vendor)
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )
