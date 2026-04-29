"""API router for Overload Web backend file handling services"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from overload_web.application.commands.file_io import (
    DeleteFileFromWorkflow,
    ListVendorFiles,
    LoadVendorFile,
    UploadFileToWorkflow,
)
from overload_web.presentation import deps

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/remote", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    vendor: str,
    loader: Annotated[Any, Depends(deps.remote_file_loader)],
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server.

    Args:
        vendor: the vendor whose server to access

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    files = ListVendorFiles.execute(
        dir=os.environ[f"{vendor.upper()}_SRC"], loader=loader
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/ftp/select", response_class=HTMLResponse)
async def select_ftp_file(
    request: Request,
    repository: Annotated[Any, Depends(deps.incoming_file_db)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    ftp: Annotated[Any, Depends(deps.remote_file_loader)],
    workflow_id: str = Form(),
    remote_file: str = Form(),
):
    vendor_dir = os.environ[f"{ftp.client.name.upper()}_SRC"]
    file_content = LoadVendorFile.execute(name=remote_file, dir=vendor_dir, loader=ftp)
    UploadFileToWorkflow(storage=storage, repo=repository).execute(
        workflow_id=workflow_id, filename=remote_file, content=file_content.content
    )
    selected = repository.list(workflow_id)
    return request.app.state.templates.TemplateResponse(
        name="pvf_partials/selected_files.html",
        request=request,
        context={"files": selected},
    )


@api_router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile,
    repository: Annotated[Any, Depends(deps.incoming_file_db)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    workflow_id: str = Form(),
):

    UploadFileToWorkflow(storage=storage, repo=repository).execute(
        workflow_id=workflow_id, filename=str(file.filename), content=file.file.read()
    )
    selected = repository.list(workflow_id)
    logger.info(f"Current file list: {selected}")
    return request.app.state.templates.TemplateResponse(
        name="pvf_partials/selected_files.html",
        request=request,
        context={"files": selected},
    )


@api_router.post("/remove", response_class=HTMLResponse)
async def remove_file(
    request: Request,
    file_id: str,
    repository: Annotated[Any, Depends(deps.incoming_file_db)],
    workflow_id: str = Form(),
):
    DeleteFileFromWorkflow.execute(id=file_id, repo=repository)
    selected = repository.list(workflow_id)
    logger.info(f"Current file list: {selected}")
    return request.app.state.templates.TemplateResponse(
        "pvf_partials/selected_files.html", {"request": request, "files": selected}
    )
