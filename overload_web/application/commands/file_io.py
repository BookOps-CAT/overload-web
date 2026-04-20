"""Application service commands for file handling."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.models import files

logger = logging.getLogger(__name__)


class ListVendorFiles:
    @staticmethod
    def execute(dir: str, loader: ports.FileLoader) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory whose files to list as a string.
            loader: Concrete implementation of `FileLoader` protocol
        Returns:
            a list of filenames contained within the given directory as strings.
        """
        files = loader.list(dir=dir)
        return files


class LoadVendorFile:
    @staticmethod
    def execute(name: str, dir: str, loader: ports.FileLoader) -> files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located as a string.
            loader: Concrete implementation of `FileLoader` protocol.

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = loader.load(name=name, dir=dir)
        return files.VendorFile(file_name=name, content=file)


class WriteFile:
    @staticmethod
    def execute(file: bytes, file_name: str, dir: str, writer: ports.FileWriter) -> str:
        """
        Write a file to a directory.

        Args:
            file: The file content to write as a bytes object.
            file_name: The name of the file as a string.
            dir: The directory where the file should be written as a string.
            writer: Concrete implementation of `FileWriter` protocol.

        Returns:
            the directory and filename where the file was written.
        """
        out_file = writer.write(file=file, file_name=file_name, dir=dir)
        return out_file


class SaveIncomingFile:
    @staticmethod
    def execute(
        file: files.VendorFile, repo: ports.SqlRepositoryProtocol
    ) -> dict[str, Any]:
        """
        Save an incoming file to temporary storage.


        Args:
            file:
                The file to save as a `files.VendorFile` object.
            repo:
                Concrete implementation of the `SqlRepositoryProtocol` for
                handling vendor files.

        Returns:
            The file's data as a dictionary.
        """
        return repo.save(file)
