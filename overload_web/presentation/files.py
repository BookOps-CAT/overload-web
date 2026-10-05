"""API router for Overload Web backend file handling services"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from overload_web.application.pvf.file_handling import (
    DeleteFileFromWorkflow,
    DownloadRemoteFile,
    ListVendorFiles,
    UploadFileToWorkflow,
)
from overload_web.presentation import pvf_deps

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/remote/list", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    retriever: Annotated[Any, Depends(pvf_deps.remote_file_retriever)],
    vendor: str,
) -> HTMLResponse:
    """
    List all files on a vendor's SFTP server.

    Args:
        retriever: a file retriever for the given vendor
        vendor: the vendor whose server to access
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
    remote_file: Annotated[str, Form(...)],
    retriever: Annotated[Any, Depends(pvf_deps.remote_file_retriever)],
    storage: Annotated[Any, Depends(pvf_deps.local_file_storage)],
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    workflow_id: Annotated[str, Form(...)],
):
    """
    Load a file from remote storage and upload it to the workflow.

    Args:
        remote_file: the name of the file to be loaded.
        retriever: a file retriever for the given vendor.
        storage: file storage for the workflow.
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
        workflow_id: the ID for the given workflow.
    Returns:
        the list of files wrapped in a `HTMLResponse` object
    """
    vendor_dir = os.environ[f"{retriever.client.name.upper()}_SRC"]
    file_content = DownloadRemoteFile.execute(
        name=remote_file, dir=vendor_dir, retriever=retriever
    )
    selected = UploadFileToWorkflow.execute(
        workflow_id=workflow_id,
        filename=remote_file,
        content=file_content.content,
        source="ftp",
        storage=storage,
        uow=uow,
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
    storage: Annotated[Any, Depends(pvf_deps.local_file_storage)],
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    workflow_id: Annotated[str, Form(...)],
):
    """
    Upload a local file to the workflow.

    Args:
        file: the file to be loaded as an `UploadFile` object.
        storage: file storage for the workflow.
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
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
        uow=uow,
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
    file_id: Annotated[str, Form(...)],
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    workflow_id: Annotated[str, Form(...)],
):
    """
    Rempve a file from the workflow.

    Args:
        file_id: the ID for the file to be removed from the workflow.
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
        workflow_id: the ID for the given workflow.

    Returns:
        the list of remaining files wrapped in a `HTMLResponse` object
    """
    selected = DeleteFileFromWorkflow.execute(
        id=file_id, uow=uow, workflow_id=workflow_id
    )
    logger.info(f"Current file list: {selected}")
    return request.app.state.templates.TemplateResponse(
        name="pvf_partials/selected_files.html",
        request=request,
        context={"files": selected},
    )
