"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from overload_web.presentation import deps, schemas, service_deps

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api", tags=["api"], lifespan=deps.lifespan)


TemplateServiceDep = Annotated[Any, Depends(service_deps.template_handler)]


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[
        schemas.OrderTemplateCreateType,
        Depends(deps.from_form(schemas.OrderTemplateCreateType)),
    ],
    service: TemplateServiceDep,
) -> HTMLResponse:
    saved_template = service.save_template(obj=template)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"template": saved_template.model_dump()},
    )


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request, template_id: str, service: TemplateServiceDep
) -> HTMLResponse:
    template = service.get_template(template_id=template_id)
    template_out = (
        {k: v for k, v in template.model_dump().items() if v} if template else {}
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/rendered_template.html",
        context={"template": template_out},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request, service: TemplateServiceDep, offset: int = 0, limit: int = 20
) -> HTMLResponse:
    template_list = service.list_templates(offset=offset, limit=limit)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/template_list.html",
        context={"templates": [i.model_dump() for i in template_list]},
    )


@api_router.patch("/template", response_class=HTMLResponse)
def update_template(
    request: Request,
    template_id: Annotated[str, Form(...)],
    template_patch: Annotated[
        schemas.OrderTemplateUpdateType,
        Depends(deps.from_form(schemas.OrderTemplateUpdateType)),
    ],
    service: TemplateServiceDep,
) -> HTMLResponse:
    updated_template = service.update_template(
        template_id=template_id, obj=template_patch
    )
    template_out = (
        {k: v for k, v in updated_template.model_dump().items() if v}
        if updated_template
        else {}
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="record_templates/template_form.html",
        context={"template": template_out},
    )


@api_router.get("/list-remote-files", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    vendor: str,
    service: Annotated[Any, Depends(service_deps.remote_file_handler)],
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server

    Args:
        vendor: the vendor whose server should be accessed

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    files = service.loader.list(dir=os.environ[f"{vendor.upper()}_SRC"])
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="files/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/process-vendor-file", response_class=HTMLResponse)
def process_vendor_file(
    request: Request,
    service: Annotated[Any, Depends(service_deps.record_processing_service)],
    files: Annotated[list[schemas.VendorFileType], Depends(deps.normalize_files)],
    order_template: Annotated[
        schemas.OrderTemplateSchemaType,
        Depends(deps.from_form(schemas.OrderTemplateSchemaType)),
    ],
    matchpoints: Annotated[
        schemas.MatchpointSchema, Depends(deps.from_form(schemas.MatchpointSchema))
    ],
) -> HTMLResponse:
    out_files = []
    template = order_template.model_dump()
    matchpoint_list = matchpoints.model_dump()
    for file in files:
        output = service.process_vendor_file(
            data=file.content, template_data=template, matchpoints=matchpoint_list
        )
        out_files.append({"file_name": file.file_name, "binary_content": output})
    return request.app.state.templates.TemplateResponse(
        request=request, name="partials/pvf_results.html", context={"files": out_files}
    )


@api_router.post("/write-local")
def write_local_file(
    vendor_file: schemas.VendorFileType,
    dir: str,
    service: Annotated[Any, Depends(service_deps.local_file_handler)],
) -> JSONResponse:
    """Write a file to a local directory."""
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )


@api_router.post("/write-remote")
def write_remote_file(
    vendor_file: schemas.VendorFileType,
    dir: str,
    vendor: str,
    service: Annotated[Any, Depends(service_deps.remote_file_handler)],
) -> JSONResponse:
    """Write a file to a remote directory."""
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )
