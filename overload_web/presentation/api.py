"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from overload_web import constants
from overload_web.application import services
from overload_web.domain import models
from overload_web.infrastructure import factories
from overload_web.presentation import schemas

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
    """Get options for session context from domain and application constants."""
    context_options = {
        "library": [i.value for i in models.bibs.RecordType],
        "collection": [i.value for i in models.bibs.Collection],
        "record_type": [i.value for i in models.bibs.RecordType],
        "vendor": [i for i in constants.VENDOR_RULES],
    }
    return JSONResponse(content={"context": context_options})


@api_router.get("/options/template")
def get_template_input_options() -> JSONResponse:
    """Get options for template inputs from application constants."""
    return JSONResponse(content={"field_constants": constants.FIELD_CONSTANTS})


@api_router.get("/list-remote")
def list_remote_files(dir: str, vendor: str) -> JSONResponse:
    """
    List all files on a vendor's SFTP server

    Args:
        dir: the directory whose files should be listed
        vendor: the vendor whose server should be accessed

    Returns:
        the list of files wrapped in a `JSONResponse` object
    """

    service = factories.create_remote_file_service(vendor=vendor)
    files = service.loader.list(dir=dir)
    return JSONResponse(content={"files": files, "directory": dir, "vendor": vendor})


@api_router.get("/load-remote")
def load_remote_files(
    file: Annotated[list[str], Query(...)], dir: str, vendor: str
) -> list[schemas.VendorFileModel]:
    """
    Load one or more files from a remote directory

    Args:
        file:
            a list of strings representing the files that should be loaded
            passed as query params.
        dir:
            the directory where the files are located
        vendor:
            the vendor whose server should be accessed

    Returns:
        the list of files wrapped in a `JSONResponse` object
    """
    """"""
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


@api_router.post("/process/{record_type}")
def process_vendor_file(
    record_type: models.bibs.RecordType,
    context: schemas.ContextModel,
    records: list[schemas.VendorFileModel],
    template_data: Optional[schemas.TemplateModel] = None,
) -> StreamingResponse:
    """
    Process a list of `VendorFileModel` objects.

    Args:
        record_type:
            the type of records being processed as an enum (either 'full' or 'order-level')
        context:
            session-specific contextual data including library, collection, and vendor
        records:
            a list of files to be process as `VendorFileModel` objects
        template_data:
            optional data to be used to update order records

    Returns:
        The processed files as a `StreamingResponse`

    """
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


@api_router.post("/process/full")
def process_full_vendor_file(
    library: str,
    collection: str,
    vendor: str,
    records: list[schemas.VendorFileModel],
) -> StreamingResponse:
    """
    Process a list of `VendorFileModel` objects.

    Args:
        context:
            session-specific contextual data including library, collection, and vendor
        records:
            a list of files to be process as `VendorFileModel` objects

    Returns:
        The processed files as a `StreamingResponse`

    """
    session_context = models.context.SessionContext(
        library=models.bibs.LibrarySystem(library),
        collection=models.bibs.Collection(collection),
        vendor=vendor,
    )
    service = services.records.FullRecordProcessingService(context=session_context)
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


@api_router.post("/process/order-level")
def process_order_vendor_file(
    library: str,
    collection: str,
    vendor: Optional[str],
    records: list[schemas.VendorFileModel],
    template_data: Optional[schemas.TemplateModel] = None,
) -> StreamingResponse:
    """
    Process a list of `VendorFileModel` objects.

    Args:
        context:
            session-specific contextual data including library, collection, and vendor
        records:
            a list of files to be process as `VendorFileModel` objects
        template_data:
            optional data to be used to update order records

    Returns:
        The processed files as a `StreamingResponse`

    """
    session_context = models.context.SessionContext(
        library=models.bibs.LibrarySystem(library),
        collection=models.bibs.Collection(collection),
        vendor=vendor,
    )
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
