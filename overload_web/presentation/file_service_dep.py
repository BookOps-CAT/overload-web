"""Dependency injection for the vendor file service."""

import logging
import os
from typing import Annotated, BinaryIO, Generator, Protocol, runtime_checkable

from fastapi import Form, UploadFile

from overload_web.application import file_service
from overload_web.files.infrastructure import local_io, sftp
from overload_web.presentation import dto

logger = logging.getLogger(__name__)


@runtime_checkable
class FileProtocol(Protocol):
    """A protocol representing a FastAPI `UploadFile` object."""

    filename: str | None
    content_type: str
    file: BinaryIO


def local_file_writer() -> Generator[file_service.FileWriterService, None, None]:
    """Create a local file writer service."""
    yield file_service.FileWriterService(writer=local_io.LocalFileWriter())


def remote_file_loader(
    vendor: str,
) -> Generator[file_service.FileTransferService, None, None]:
    """Create an SFTP file loader service."""
    yield file_service.FileTransferService(
        loader=sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor)
    )


def remote_file_writer(
    vendor: str,
) -> Generator[file_service.FileWriterService, None, None]:
    """Create an SFTP file writer service."""
    yield file_service.FileWriterService(
        writer=sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor)
    )


def normalize_files(
    files: Annotated[list[UploadFile] | list[str], Form(...)],
    vendor: Annotated[str, Form(...)],
) -> list[dto.VendorFileModel]:
    """
    Normalize a list of files loaded from either a remote or local directory.

    This function loads remote files from an SFTP server based on a list of
    file names if necessary. All files are returned `VendorFileModel` objects.

    Args:
        files: list of either `UploadFile` objects or remote file names
        vendor: the vendor whose server to access
    Returns:
        a list of `VendorFileModel` objects
    """
    remote_files = []
    local_files = []
    for file in files:
        if isinstance(file, FileProtocol):
            local_files.append(
                dto.VendorFileModel(
                    file_name=str(file.filename), content=file.file.read()
                )
            )
        else:
            remote_files.append(file)

    file_list = []
    if local_files:
        file_list.extend(local_files)
    if remote_files and vendor:
        vendor_dir = os.environ[f"{vendor.upper()}_SRC"]
        service = file_service.FileTransferService(
            loader=sftp.SFTPFileLoader.create_loader_for_vendor(vendor)
        )
        loaded_files = [
            service.loader.load(name=f, dir=vendor_dir)
            for f in remote_files
            if isinstance(f, str)
        ]
        file_list.extend([dto.VendorFileModel(**f.__dict__) for f in loaded_files])
    return file_list
