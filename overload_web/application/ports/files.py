from __future__ import annotations

from typing import Protocol, runtime_checkable

from overload_web.domain.models import files


@runtime_checkable
class FileLoader(Protocol):
    """
    A protocol for a service which loads .mrc files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def list(self, dir: str) -> list[str]: ...  # pragma: no branch

    """
    List available files.

    Args:
        dir: the directory whose files to list

    Returns:
        a list of file names as strings
    """

    def load(self, name: str, dir: str) -> files.VendorFile: ...  # pragma: no branch

    """
    Load the content of a specific file.

    Args:
        name: the name of the file to load
        dir: the directory where the file is located

    Returns:
        the specified file as a `VendorFile` object
    """


@runtime_checkable
class FileWriter(Protocol):
    """
    A protocol for a service which writes .mrc files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def write(self, file: files.VendorFile, dir: str) -> str: ...  # pragma: no branch

    """
    Write a content to a specific file.

    Args:
        file: the file to write as a `VendorFile` object
        dir: the directory where the file should be written

    Returns:
        the name of the file that has just been written
    """
