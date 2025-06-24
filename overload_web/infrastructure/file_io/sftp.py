"""
FTP/SFTP file I/O implementations for Overload.

This module contains classes to load files from and write files to remote FTP/SFTP
servers. These classes are used when file operations need to happen on a remote
server accessible via FTP/SFTP. The classes within this module use the
BookOps/file-retriever library.
"""

import os
from typing import Union

from file_retriever import Client

from overload_web.application import dto
from overload_web.infrastructure.file_io import factories


class SFTPFileLoader:
    """
    Loads files from a remote FTP/SFTP server.

    Implements the `FileLoader` protocol using the file-retriever library
    to connect to an FTP/SFTP server.
    """

    def __init__(self, client: Client, base_dir: Union[str, None] = None) -> None:
        self.client = client
        if base_dir is None:
            self.base_dir: str = os.environ[f"{client.name.upper()}_DST"]
        else:
            self.base_dir = base_dir

    def list(self) -> list[dto.file.FileMetadataDTO]:
        file_list = self.client.list_file_info(remote_dir=self.base_dir)
        return [factories.file_to_metadata_dto(i) for i in file_list]

    def load(self, name: str) -> dto.file.FileContentDTO:
        file_info = self.client.get_file_info(file_name=name, remote_dir=self.base_dir)
        file = self.client.get_file(file=file_info, remote_dir=self.base_dir)
        return factories.file_to_content_dto(file=file)


class SFTPFileWriter:
    """
    Writes files to a remote FTP/SFTP server.

    Implements the `FileWriter` protocol using the file-retriever library
    to connect to an FTP/SFTP server.
    """

    def __init__(self, client: Client, base_dir: Union[str, None] = None) -> None:
        self.client = client
        if base_dir is None:
            self.base_dir: str = os.environ[f"{client.name.upper()}_DST"]
        else:
            self.base_dir = base_dir

    def write(self, file: dto.file.FileContentDTO) -> str:
        converted_file = factories.content_dto_to_file(content_dto=file)
        out_file = self.client.put_file(
            file=converted_file, check=False, remote=True, dir=self.base_dir
        )
        return getattr(out_file, "file_name", file.file_id)
