"""
Local file I/O implementations for Overload.

This module contains classes to load files from and write files to the local filesystem.
Typically used for temporary or persistent file storage on the server hosting the app.
The classes within this module are concrete implementations of the `FileLoader` and
`FileWriter` protocols within the domain model.
"""

import os

from overload_web.domain.models import files


class LocalFileLoader:
    """
    Loads files from the local filesystem.

    This class implements the `FileLoader` protocol by listing and loading file
    contents from a specific directory on a local computer.
    """

    def list(self, dir: str) -> list[str]:
        """List available files in a local directory."""
        return os.listdir(dir)

    def load(self, name: str, dir: str) -> files.VendorFile:
        """Load a file from a local directory."""
        with open(os.path.join(dir, name), "rb") as fh:
            file_dto = files.VendorFile(content=fh.read(), file_name=name)
        return file_dto


class LocalFileWriter:
    """
    Writes files to the local filesystem.

    This class implements the `FileWriter` protocol by writing binary content
    to files within a specific directory on a local computer.
    """

    def write(self, file: files.VendorFile, dir: str) -> str:
        """Write a file to a local directory."""
        path = os.path.join(dir, file.file_name)
        with open(path, "wb") as f:
            f.write(file.content)
        return path
