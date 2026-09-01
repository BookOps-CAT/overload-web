"""API router for Overload Web backend file handling services"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from overload_web.application.pvf.file_handling import (
    DeleteFileFromWorkflow,
    ListVendorFiles,
    LoadVendorFile,
    UploadFileToWorkflow,
)
from overload_web.presentation import deps

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/remote/list", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    vendor: str,
    retriever: Annotated[Any, Depends(deps.remote_file_retriever)],
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server.

    Args:
        vendor: the vendor whose server to access
        retriever: a file retriever for the given vendor

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    files = ListVendorFiles.execute(
        dir=os.environ[f"{vendor.upper()}_SRC"], retriever=retriever
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/remote/select", response_class=HTMLResponse)
def select_ftp_file(
    request: Request,
    repository: Annotated[Any, Depends(deps.incoming_file_db)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    retriever: Annotated[Any, Depends(deps.remote_file_retriever)],
    workflow_id: Annotated[str, Form(...)],
    remote_file: Annotated[str, Form(...)],
):
    """
    Load a file from remote storage and upload it to the workflow.

    Args:
        repository: the repository where file data is written.
        storage: file storage for the workflow.
        retriever: a file retriever for the given vendor.
        workflow_id: the ID for the given workflow.
        remote_file: the name of the file to be loaded.

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    vendor_dir = os.environ[f"{retriever.client.name.upper()}_SRC"]
    file_content = LoadVendorFile.execute(
        name=remote_file, dir=vendor_dir, retriever=retriever
    )
    selected = UploadFileToWorkflow.execute(
        workflow_id=workflow_id,
        filename=remote_file,
        content=file_content.content,
        source="ftp",
        storage=storage,
        repo=repository,
    )
    return request.app.state.templates.TemplateResponse(
        name="pvf_partials/selected_files.html",
        request=request,
        context={"files": selected},
    )


@api_router.post("/upload", response_class=HTMLResponse)
def upload_file(
    request: Request,
    file: UploadFile,
    repository: Annotated[Any, Depends(deps.incoming_file_db)],
    storage: Annotated[Any, Depends(deps.local_file_storage)],
    workflow_id: Annotated[str, Form(...)],
):
    """
    Upload a local file to the workflow.

    Args:
        file: the file to be loaded as an `UploadFile` object.
        repository: the repository where file data is written.
        storage: file storage for the workflow.
        workflow_id: the ID for the given workflow.

    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    selected = UploadFileToWorkflow.execute(
        workflow_id=workflow_id,
        filename=str(file.filename),
        content=file.file.read(),
        source="local",
        storage=storage,
        repo=repository,
    )
    logger.info(f"Current file list: {selected}")
    return request.app.state.templates.TemplateResponse(
        name="pvf_partials/selected_files.html",
        request=request,
        context={"files": selected},
    )


@api_router.post("/remove", response_class=HTMLResponse)
def remove_file(
    request: Request,
    repository: Annotated[Any, Depends(deps.incoming_file_db)],
    file_id: Annotated[str, Form(...)],
    workflow_id: Annotated[str, Form(...)],
):
    """
    Rempve a file from the workflow.

    Args:
        repository: the repository where file data is written.
        file_id: the ID for the file to be removed from the workflow.
        workflow_id: the ID for the given workflow.

    Returns:
        the list of remaining files wrapped in a `HTMLResponse` object
    """
    selected = DeleteFileFromWorkflow.execute(
        id=file_id, repo=repository, workflow_id=workflow_id
    )
    logger.info(f"Current file list: {selected}")
    return request.app.state.templates.TemplateResponse(
        name="pvf_partials/selected_files.html",
        request=request,
        context={"files": selected},
    )
