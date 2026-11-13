"""API router for Overload Web backend file handling services."""

from __future__ import annotations

import io
import logging
import os
import urllib.parse
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from overload_web.application.pvf import queries
from overload_web.application.pvf.file_handling import (
    DownloadVendorFile,
    ListVendorFiles,
)
from overload_web.domain.pvf import commands
from overload_web.presentation import pvf_deps
from overload_web.presentation.templates import templates

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.get("/remote/list", response_class=HTMLResponse)
def list_remote_files(
    request: Request,
    retriever: Annotated[Any, Depends(pvf_deps.remote_file_retriever)],
    vendor: str,
) -> HTMLResponse:
    """List all files on a vendor's SFTP server.

    Args:
        request: the HTTP request sent by the app
        retriever: a file retriever for the given vendor
        vendor: the vendor whose server to access
    Returns:
        the list of files wrapped in a `HTMLResponse` object

    """
    files = ListVendorFiles.execute(
        dir=os.environ[f"{vendor.upper()}_SRC"], retriever=retriever
    )
    return templates.TemplateResponse(
        request=request,
        name="pvf/partials/files/remote_list.html",
        context={"files": files, "vendor": vendor},
    )


@api_router.post("/remote/select", response_class=Response)
def select_ftp_file(
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    remote_file: Annotated[str, Form(...)],
    retriever: Annotated[Any, Depends(pvf_deps.remote_file_retriever)],
    workflow_id: Annotated[str, Form(...)],
) -> Response:
    """Upload a file from an SFTP client to the workflow.

    Args:
        bus: a `ports.MessageBusPort` object used by the workflow
        remote_file: the name of the file to be loaded.
        retriever: a file retriever for the given vendor.
        workflow_id: the ID for the given workflow.

    Returns:
        204 response with 'workflowFilesChanged' in headers for htmx trigger.

    """
    vendor_dir = os.environ[f"{retriever.client.name.upper()}_SRC"]
    file_content = DownloadVendorFile.execute(
        name=remote_file, dir=vendor_dir, retriever=retriever
    )
    bus.send(
        commands.UploadFileToWorkflow(
            workflow_id=workflow_id,
            filename=remote_file,
            content=file_content.content,
            source="ftp",
        )
    )
    return Response(status_code=204, headers={"HX-Trigger": "workflowFilesChanged"})


@api_router.get("/list/processed-files", response_class=HTMLResponse)
def get_processed_file_list(
    request: Request, batch_id: str, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> HTMLResponse:
    """Get a list of all processed files for a batch.

    Args:
        request: the HTTP request sent by the app
        batch_id: the ID for the given processed batch.
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.

    Returns:
        the list of files wrapped in an HTMLResponse object

    """
    files = queries.get_processed_file_list(uow=uow, batch_id=batch_id)
    return templates.TemplateResponse(
        name="pvf/partials/files/processed_list.html",
        request=request,
        context={"files": files},
    )


@api_router.get("/download/{file_id}", response_class=StreamingResponse)
def download_file(
    file_id: str, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> StreamingResponse:
    """Download a file.

    Args:
        file_id: ID of the file to be downloaded.
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.

    Returns:
        the list of files wrapped in an HTMLResponse object

    """
    file = queries.get_processed_file(uow=uow, file_id=file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    encoded_name = urllib.parse.quote(file.filename)
    byte_stream = io.BytesIO(file.content)
    return StreamingResponse(
        content=byte_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
            "Content-Length": str(len(file.content)),
        },
    )


@api_router.get("/list", response_class=HTMLResponse)
def list_workflow_files(
    request: Request, uow: Annotated[Any, Depends(pvf_deps.get_uow)], workflow_id: str
) -> HTMLResponse:
    """List all files associated with a workflow ID.

    Args:
        request: the HTTP request sent by the app
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
        workflow_id: the ID for the given workflow.

    Returns:
        the list of files wrapped in a `HTMLResponse` object

    """
    files = queries.list_workflow_files(uow=uow, workflow_id=workflow_id)
    return templates.TemplateResponse(
        name="pvf/partials/files/selected_list.html",
        request=request,
        context={"files": files},
    )


@api_router.post("/remove", response_class=Response)
def remove_file(
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    file_id: Annotated[str, Form(...)],
    workflow_id: Annotated[str, Form(...)],
) -> Response:
    """Rempve a file from the workflow.

    Args:
        bus: a `ports.MessageBusPort` object used by the workflow
        file_id: the ID for the file to be removed from the workflow.
        workflow_id: the ID for the given workflow.

    Returns:
        204 response with 'workflowFilesChanged' in headers for htmx trigger.

    """
    bus.send(commands.DeleteFileFromWorkflow(workflow_id=workflow_id, file_id=file_id))
    return Response(status_code=204, headers={"HX-Trigger": "workflowFilesChanged"})


@api_router.post("/upload", response_class=Response)
def upload_file(
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    file: UploadFile,
    workflow_id: Annotated[str, Form(...)],
) -> Response:
    """Upload a local file to the workflow.

    Args:
        bus: a `ports.MessageBusPort` object used by the workflow
        file: the file to be loaded as an `UploadFile` object.
        workflow_id: the ID for the given workflow.

    Returns:
        204 response with 'workflowFilesChanged' in headers for htmx trigger.

    """
    bus.send(
        commands.UploadFileToWorkflow(
            workflow_id=workflow_id,
            filename=str(file.filename),
            content=file.file.read(),
            source="local",
        )
    )
    return Response(status_code=204, headers={"HX-Trigger": "workflowFilesChanged"})
