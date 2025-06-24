"""
Local file I/O implementations for Overload.

This module contains classes to load files from and write files to the local filesystem.
Typically used for temporary or persistent file storage on the server hosting the app.
The classes within this module are concrete implementations of the `FileLoader` and
`FileWriter` protocols within the domain model.
"""

import os

from overload_web.domain import models


class LocalFileLoader:
    """
    Loads files from the local filesystem.

    This class implements the `FileLoader` protocol by listing and loading file
    contents from a specific directory on a local computer.
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def list(self) -> list[str]:
        return os.listdir(self.base_dir)

    def load(self, name: str) -> models.files.VendorFile:
        with open(os.path.join(self.base_dir, name), "rb") as fh:
            file_dto = models.files.VendorFile.create(content=fh.read(), file_name=name)
        return file_dto


class LocalFileWriter:
    """
    Writes files to the local filesystem.

    This class implements the `FileWriter` protocol by writing binary content
    to files within a specific directory on a local computer.
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def write(self, file: models.files.VendorFile) -> str:
        path = os.path.join(self.base_dir, file.file_name)
        with open(path, "wb") as f:
            f.write(file.content)
        return path
