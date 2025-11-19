"""
FTP/SFTP file I/O implementations for Overload.

This module contains classes to load files from and write files to remote FTP/SFTP
servers. These classes are used when file operations need to happen on a remote
server accessible via FTP/SFTP. The classes within this module use the
BookOps/file-retriever library.
"""

from __future__ import annotations

import io
import os

from file_retriever import Client, File

from overload_web.files.domain import vendor_files


class SFTPFileLoader:
    """
    Loads files from a remote FTP/SFTP server.

    Implements the `FileLoader` protocol using the file-retriever library
    to connect to an FTP/SFTP server.
    """

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(self, dir: str) -> list[str]:
        return self.client.list_files(remote_dir=dir)

    def load(self, name: str, dir: str) -> vendor_files.VendorFile:
        file_info = self.client.get_file_info(file_name=name, remote_dir=dir)
        file = self.client.get_file(file=file_info, remote_dir=dir)
        file.file_stream.seek(0)
        return vendor_files.VendorFile(
            content=file.file_stream.read(), file_name=file.file_name
        )

    @classmethod
    def create_loader_for_vendor(cls, vendor: str) -> SFTPFileLoader:
        client = Client(
            name=vendor.upper(),
            username=os.environ[f"{vendor.upper()}_USER"],
            password=os.environ[f"{vendor.upper()}_PASSWORD"],
            host=os.environ[f"{vendor.upper()}_HOST"],
            port=os.environ[f"{vendor.upper()}_PORT"],
        )
        return SFTPFileLoader(client=client)


class SFTPFileWriter:
    """
    Writes files to a remote FTP/SFTP server.

    Implements the `FileWriter` protocol using the file-retriever library
    to connect to an FTP/SFTP server.
    """

    def __init__(self, client: Client) -> None:
        self.client = client

    def write(self, file: vendor_files.VendorFile, dir: str) -> str:
        converted_file = File(
            file_name=file.file_name,
            file_stream=io.BytesIO(file.content),
            file_mtime=0,
            file_mode=None,
            file_size=0,
        )
        out_file = self.client.put_file(file=converted_file, remote=True, dir=dir)
        return getattr(out_file, "file_name", file.file_name)

    @classmethod
    def create_writer_for_vendor(cls, vendor: str) -> SFTPFileWriter:
        client = Client(
            name=vendor.upper(),
            username=os.environ[f"{vendor.upper()}_USER"],
            password=os.environ[f"{vendor.upper()}_PASSWORD"],
            host=os.environ[f"{vendor.upper()}_HOST"],
            port=os.environ[f"{vendor.upper()}_PORT"],
        )
        return SFTPFileWriter(client=client)
