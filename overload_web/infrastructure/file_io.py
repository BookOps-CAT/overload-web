"""
Local and FTP/SFTP file I/O implementations for Overload.

This module contains classes to load files from and write files to local
directories and remote FTP/SFTP servers. The classes that interact with remote
directories within this module use the BookOps/file-retriever library.
The classes within this module are concrete implementations of the `FileLoader` and
`FileWriter` protocols within the domain model.
"""

from __future__ import annotations

import io
import os

from file_retriever import Client, File


class LocalFileLoader:
    """
    Loads files from the local filesystem.

    This class implements the `FileLoader` protocol by listing and loading file
    contents from a specific directory on a local computer.
    """

    def list(self, dir: str) -> list[str]:
        """List available files in a local directory."""
        return os.listdir(dir)

    def load(self, name: str, dir: str) -> bytes:
        """Load a file from a local directory."""
        with open(os.path.join(dir, name), "rb") as fh:
            file = fh.read()
        return file


class LocalFileWriter:
    """
    Writes files to the local filesystem.

    This class implements the `FileWriter` protocol by writing binary content
    to files within a specific directory on a local computer.
    """

    def write(self, file: bytes, file_name: str, dir: str) -> str:
        """Write a file to a local directory."""
        path = os.path.join(dir, file_name)
        with open(path, "wb") as f:
            f.write(file)
        return path


class SFTPFileLoader:
    """
    Loads files from a remote FTP/SFTP server.

    Implements the `FileLoader` protocol using the file-retriever library
    to connect to an FTP/SFTP server.
    """

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(self, dir: str) -> list[str]:
        """List files in a remote directory."""
        return self.client.list_files(remote_dir=dir)

    def load(self, name: str, dir: str) -> bytes:
        """Load a file from a remote directory."""
        file_info = self.client.get_file_info(file_name=name, remote_dir=dir)
        file = self.client.get_file(file=file_info, remote_dir=dir)
        file.file_stream.seek(0)
        return file.file_stream.read()

    @classmethod
    def create_loader_for_vendor(cls, vendor: str) -> SFTPFileLoader:
        """Create an `SFTPFileLoader` for a specific vendor based on envars."""
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

    def write(self, file: bytes, file_name: str, dir: str) -> str:
        """Write a file to a remote directory."""
        converted_file = File(
            file_name=file_name,
            file_stream=io.BytesIO(file),
            file_mtime=0,
            file_mode=None,
            file_size=0,
        )
        out_file = self.client.put_file(file=converted_file, remote=True, dir=dir)
        return getattr(out_file, "file_name", file_name)
