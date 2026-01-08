"""Application service handling file operations.

Uses `FileLoader` and `FileWriter` domain protocols.
"""

from __future__ import annotations

import logging

from overload_web.files.domain import file_protocols, vendor_files

logger = logging.getLogger(__name__)


class FileTransferService:
    """Handles file transfer operations through `FileLoader`."""

    def __init__(self, loader: file_protocols.FileLoader):
        """
        Initialize `FileTransferService`.

        Args:
            loader: concrete implementation of `FileLoader` protocol
        """
        self.loader = loader

    def list_files(self, dir: str) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory whose files to list.

        Returns:
            a list of filenames contained within the given directory as strings.
        """
        files = self.loader.list(dir=dir)
        logger.info(f"Files in {dir}: {files}")
        return files

    def load_file(self, name: str, dir: str) -> vendor_files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located.

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = self.loader.load(name=name, dir=dir)
        logger.info(f"File loaded: {name}")
        return file


class FileWriterService:
    """Handles file writing operations through `FileWriter`."""

    def __init__(self, writer: file_protocols.FileWriter):
        """
        Initialize `FileWriterService`.

        Args:
            writer: concrete implementation of `FileWriter` protocol
        """
        self.writer = writer

    def write_marc_file(self, file: vendor_files.VendorFile, dir: str) -> str:
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
