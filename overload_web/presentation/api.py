"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session

from overload_web import config
from overload_web.application import services
from overload_web.infrastructure import db
from overload_web.presentation import deps, schemas

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api", tags=["api"])

templates = config.get_templates()

SessionDep = Annotated[Session, Depends(deps.get_session)]


@api_router.on_event("startup")
def startup_event():
    deps.create_db_and_tables()


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[
        db.tables.OrderTemplateCreate, Depends(db.tables.OrderTemplateCreate.from_form)
    ],
    session: SessionDep,
) -> HTMLResponse:
    valid_template = db.tables.OrderTemplate.model_validate(template)
    service = services.template.OrderTemplateService(session=session)
    saved_template = service.save_template(obj=valid_template)
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"template": saved_template.model_dump()},
    )


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request, template_id: str, session: SessionDep
) -> HTMLResponse:
    service = services.template.OrderTemplateService(session=session)
    template = service.get_template(template_id=template_id)
    template_out = (
        {k: v for k, v in template.model_dump().items() if v} if template else {}
    )
    return templates.TemplateResponse(
        request=request,
        name="record_templates/rendered_template.html",
        context={"template": template_out},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request, session: SessionDep, offset: int = 0, limit: int = 20
) -> HTMLResponse:
    service = services.template.OrderTemplateService(session=session)
    template_list = service.list_templates(offset=offset, limit=limit)
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_list.html",
        context={"templates": [i.model_dump() for i in template_list]},
    )


@api_router.patch("/template", response_class=HTMLResponse)
def update_template(
    request: Request,
    template_id: Annotated[str, Form(...)],
    template_patch: Annotated[
        db.tables.OrderTemplateUpdate, Depends(db.tables.OrderTemplateUpdate.from_form)
    ],
    session: SessionDep,
) -> HTMLResponse:
    service = services.template.OrderTemplateService(session=session)
    template = service.get_template(template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="OrderTemplate not found")
    patch_data = template_patch.model_dump(exclude_unset=True)
    template.sqlmodel_update(patch_data)
    updated_template = service.save_template(obj=template)
    return templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"template": updated_template.model_dump()},
    )


@api_router.get("/list-remote-files", response_class=HTMLResponse)
def list_remote_files(request: Request, vendor: str) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server

    Args:
        vendor: the vendor whose server should be accessed

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    service = services.file.FileTransferService.create_remote_file_service(vendor)
    files = service.loader.list(dir=os.environ[f"{vendor.upper()}_SRC"])
    return templates.TemplateResponse(
        request=request,
        name="files/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/process-vendor-file", response_class=HTMLResponse)
def process_vendor_file(
    request: Request,
    service: Annotated[
        services.records.RecordProcessingService, Depends(deps.get_record_service)
    ],
    files: Annotated[list[schemas.VendorFileModel], Depends(deps.normalize_files)],
    template_input: Annotated[
        schemas.OrderTemplateSchema, Depends(schemas.OrderTemplateSchema.from_form)
    ],
    matchpoints: Annotated[
        schemas.MatchpointSchema, Depends(schemas.MatchpointSchema.from_form)
    ],
) -> HTMLResponse:
    out_files = []
    for file in files:
        bibs = service.parse(data=file.content)
        processed_bibs = service.process_records(
            records=bibs,
            template_data=template_input.model_dump(),
            matchpoints=matchpoints.model_dump(),
        )
        marc_binary = service.write_marc_binary(records=processed_bibs)
        out_files.append({"file_name": file.file_name, "binary_content": marc_binary})
    return templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context={"files": out_files}
    )


@api_router.post("/write-local")
def write_local_file(vendor_file: schemas.VendorFileModel, dir: str) -> JSONResponse:
    """Write a file to a local directory."""
    service = services.file.FileTransferService.create_local_file_service()
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/write-remote")
def write_remote_file(
    vendor_file: schemas.VendorFileModel, dir: str, vendor: str
) -> JSONResponse:
    """Write a file to a remote directory."""
    service = services.file.FileTransferService.create_remote_file_service(
        vendor=vendor
    )
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )
