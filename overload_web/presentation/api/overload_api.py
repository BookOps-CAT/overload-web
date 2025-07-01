"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from overload_web import constants
from overload_web.application import services
from overload_web.domain import models
from overload_web.infrastructure import factories
from overload_web.presentation.api import schemas

logger = logging.getLogger(__name__)
api_router = APIRouter()


@api_router.get("/")
def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        JSON response indicating the application is active.
    """
    return JSONResponse(content={"app": "Overload Web"})


@api_router.get("/options/context")
def get_context_options() -> JSONResponse:
    context_options = {
        "library": [i.value for i in models.bibs.RecordType],
        "collection": [i.value for i in models.bibs.Collection],
        "record_type": [i.value for i in models.bibs.RecordType],
        "vendor": [i for i in constants.VENDOR_RULES],
    }
    return JSONResponse(content={"context": context_options})


@api_router.get("/options/template")
def get_template_input_options() -> JSONResponse:
    return JSONResponse(content={"field_constants": constants.FIELD_CONSTANTS})


@api_router.get("/list_files")
def list_files(dir: str, remote: bool, vendor: Optional[str] = None) -> JSONResponse:
    """List all files available in a specific directory"""
    service = factories.create_file_service(remote=remote, vendor=vendor)
    files = service.loader.list(dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": files, "directory": dir}
    )


@api_router.get("/load_files")
def load_files(
    file: Annotated[list[str], Query(...)],
    dir: str,
    remote: bool,
    vendor: Optional[str] = None,
) -> list[schemas.VendorFileModel]:
    """Load one or more files"""
    service = factories.create_file_service(remote=remote, vendor=vendor)
    files = [service.loader.load(name=f, dir=dir) for f in file]
    return [schemas.VendorFileModel(**i.__dict__) for i in files]


@api_router.post("/process/{record_type}")
def vendor_file_process(
    record_type: models.bibs.RecordType,
    context: schemas.ContextModel,
    records: list[schemas.VendorFileModel],
    template_data: Optional[schemas.TemplateModel] = None,
) -> StreamingResponse:
    service: (
        services.records.FullRecordProcessingService
        | services.records.OrderRecordProcessingService
    )
    session_context = models.context.SessionContext(
        library=context.library, collection=context.collection, vendor=context.vendor
    )
    if str(record_type) == "full":
        service = services.records.FullRecordProcessingService(context=session_context)
    else:
        template = template_data.__dict__
        matchpoints = [i for i in list(template["matchpoints"].__dict__.values()) if i]
        template["matchpoints"] = matchpoints
        service = services.records.OrderRecordProcessingService(
            context=session_context, template=template
        )
    bibs = service.parse(data=records[0].content)
    processed_bibs = service.process_records(records=bibs)
    marc_binary = service.write_marc_binary(records=processed_bibs)
    return StreamingResponse(
        marc_binary,
        media_type="application/marc",
        headers={
            "Content-Disposition": f"attachment; filename={records[0].file_name}_out.mrc"
        },
    )


@api_router.post("/write_file")
def write_file(
    vendor_file: schemas.VendorFileModel,
    dir: str,
    remote: bool,
    vendor: Optional[str],
) -> JSONResponse:
    service = factories.create_file_service(remote=remote, vendor=vendor)
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )
