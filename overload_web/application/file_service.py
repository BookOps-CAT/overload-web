"""Application service handling file operations.

Uses `FileLoader` and `FileWriter` domain protocols.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from overload_web.infrastructure import local_io, sftp

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.domain_models import files
    from overload_web.domain_protocols import file_io
logger = logging.getLogger(__name__)


class FileTransferService:
    """Handles file transfer operations through `FileLoader` and `FileWriter`."""

    def __init__(self, loader: file_io.FileLoader, writer: file_io.FileWriter):
        """
        Initialize `FileTransferService` obj.

        Args:
            loader: concrete implementation of `FileLoader` protocol
            writer: concrete implementation of `FileWriter` protocol
        """
        self.loader = loader
        self.writer = writer

    def list_files(self, dir: str) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory to list files from.

        Returns:
            a list of filenames contained within the given directory
        """
        files = self.loader.list(dir=dir)
        logger.info(f"Files in {dir}: {files}")
        return files

    def load_file(self, name: str, dir: str) -> files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file.
            dir: The directory to load the file from.

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = self.loader.load(name=name, dir=dir)
        logger.info(f"File loaded: {name}")
        return file

    def write_marc_file(self, file: files.VendorFile, dir: str) -> str:
        """
        Write a file to a directory.

        Args:
            file: The file to write as a `files.VendorFile` object.
            dir: The directory where the file should be written.

        Returns:
            the directory and filename where the file was written.
        """
        out_file = self.writer.write(file=file, dir=dir)
        logger.info(f"Writing file to directory: {dir}/{out_file}")
        return out_file

    @classmethod
    def create_local_file_service(cls) -> FileTransferService:
        """Create a `FileTransferService object for local file handling."""
        return FileTransferService(
            loader=local_io.LocalFileLoader(),
            writer=local_io.LocalFileWriter(),
        )

    @classmethod
    def create_remote_file_service(cls, vendor: str) -> FileTransferService:
        """
        Create a `FileTransferService` object to handle file operations on a
        vendor's remote storage.

        Args:
            vendor: the name of the vendor as a string.

        Returns:
            A `FileTransferService` object for the vendor's remote storage.
        """
        return FileTransferService(
            loader=sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor),
            writer=sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor),
        )
