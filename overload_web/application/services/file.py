"""Application service handling file operations.

Uses `FileLoader` and `FileWriter` domain protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from overload_web.infrastructure import file_io

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.domain import models, protocols


class FileTransferService:
    """Handles file transfer operations through file loader and writer."""

    def __init__(
        self, loader: protocols.file_io.FileLoader, writer: protocols.file_io.FileWriter
    ):
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
            a list of files in the given directory
        """
        return self.loader.list(dir=dir)

    def load_file(self, name: str, dir: str) -> models.files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file.
            dir: The directory to load the file from.

        Returns:
            The loaded file as a `models.files.VendorFile` object.
        """
        return self.loader.load(name=name, dir=dir)

    def write_marc_file(self, file: models.files.VendorFile, dir: str) -> str:
        """
        Write a file to a directory

        Args:
            file: The file to write as a `models.files.VendorFile` object
            dir: The directory where the file should be written

        Returns:
            the directory and filename where the file was written.
        """
        return self.writer.write(file=file, dir=dir)

    @classmethod
    def create_local_file_service(cls) -> FileTransferService:
        return FileTransferService(
            loader=file_io.local.LocalFileLoader(),
            writer=file_io.local.LocalFileWriter(),
        )

    @classmethod
    def create_remote_file_service(cls, vendor: str) -> FileTransferService:
        return FileTransferService(
            loader=file_io.sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor),
            writer=file_io.sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor),
        )
