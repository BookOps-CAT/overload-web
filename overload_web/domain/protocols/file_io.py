"""Protocols for file I/O services within Overload.

The protocols within this module support reading and writing files
and allow for the `FileProcessorService` to remain decoupled from any
specific data source.
"""

from typing import Protocol, runtime_checkable

from overload_web.application import dto


@runtime_checkable
class FileLoader(Protocol):
    """
    A protocol for a service which loads .mrc files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def list(self) -> list[dto.file.FileMetadataDTO]: ...

    """
    List available files:

    Args:
        None
    
    Returns:
        a list of files represented by their file metadata as 
        `FileMetadataDTO` objects
    """

    def load(self, name: str) -> dto.file.FileContentDTO: ...

    """
    Load the content of a specific file.

    Args:
        file_id: the id of a specific file

    Returns:
        the content of the specified file represented as a 
        `FileContentDTO` object
    """


@runtime_checkable
class FileWriter(Protocol):
    """
    A protocol for a service which writes .mrc files for use within Overload.

    Implementations may interact with an FTP/SFTP server or a local file directory.
    """

    def write(self, file: dto.file.FileContentDTO) -> str: ...

    """
    Write a content to a specific file.

    Args:
        file_id: the id of the file to be written.
        content: the content of the file as bytes.

    Returns:
        the ID of the file that has just been written
    """
