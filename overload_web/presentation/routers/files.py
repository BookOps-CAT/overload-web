"""API router for Overload Web backend services."""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from overload_web.application.commands.file_io import ListVendorFiles
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
