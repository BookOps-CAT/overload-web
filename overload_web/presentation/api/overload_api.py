"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from overload_web.application import services
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


@api_router.get("/list-remote")
def list_remote_files(dir: str, vendor: str) -> JSONResponse:
    """List all files on a vendor's SFTP server"""
    service = factories.create_remote_file_service(vendor=vendor)
    files = service.loader.list(dir=dir)
    return JSONResponse(content={"files": files, "directory": dir, "vendor": vendor})


@api_router.get("/load-remote")
def load_remote_files(
    file: Annotated[list[str], Query(...)], dir: str, vendor: str
) -> list[schemas.VendorFileModel]:
    """Load one or more files from a remote directory"""
    service = factories.create_remote_file_service(vendor=vendor)
    files = [service.loader.load(name=f, dir=dir) for f in file]
    return [schemas.VendorFileModel(**i.__dict__) for i in files]


@api_router.post("/load-local")
def load_local_files(
    file: Annotated[list[UploadFile], File(...)],
) -> list[schemas.VendorFileModel]:
    """Upload local files for processing"""
    return [
        schemas.VendorFileModel.create(file_name=i.filename, content=i.file.read())
        for i in file
    ]


@api_router.post("/vendor_file")
def vendor_file_process(
    file: Annotated[UploadFile, File(...)],
    library: Annotated[str, Form()],
    collection: Annotated[Optional[str], Form()] = None,
    form_data: schemas.TemplateModel = Depends(schemas.TemplateModel.from_form_data),
) -> StreamingResponse:
    """
    Processes an uploaded vendor MARC file, optionally applying a template.

    Args:
        file: the uploaded MARC file to process.
        library: the library to whom the records belong ("bpl" or "nypl").
        collection: optional library collection.
        form_data: a `TemplateModel` containing template fields and matchpoints.

    Returns:
        A list of processed bib records.
    """
    template_data = {k: v for k, v in form_data.__dict__.items() if k != "matchpoints"}
    service = services.records.RecordProcessingService(
        library=library,
        template=template_data,
        matchpoints=form_data.matchpoints.as_list(),
    )
    bibs = service.parse(data=file.file)
    processed_bibs = service.process_records(records=bibs)
    marc_binary = service.write_marc_binary(records=processed_bibs)
    return StreamingResponse(
        marc_binary,
        media_type="application/marc",
        headers={
            "Content-Disposition": f"attachment; filename={file.filename}_out.mrc"
        },
    )


@api_router.post("/write-local")
def write_local_file(
    vendor_file: schemas.VendorFileModel,
    dir: str,
) -> JSONResponse:
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
    service = factories.create_remote_file_service(vendor=vendor)
    out_files = service.writer.write(file=vendor_file, dir=dir)
    return JSONResponse(
        content={"app": "Overload Web", "files": out_files, "directory": dir}
    )
