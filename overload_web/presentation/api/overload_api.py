"""API router for Overload Web backend services.

Includes endpoints for root and processing vendor MARC files.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from overload_web.application import services
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
    bibs = services.read_marc_binary(file_data=file.file, library=library)
    matched_bibs = services.match_bibs(
        bibs=bibs, library=library, matchpoints=form_data.matchpoints.as_list()
    )
    processed_bibs = services.attach_template(bibs=matched_bibs, template=template_data)
    marc_binary = services.write_marc_binary(bibs=processed_bibs)
    return StreamingResponse(
        marc_binary,
        media_type="application/marc",
        headers={
            "Content-Disposition": f"attachment; filename={file.filename}_out.mrc"
        },
    )
