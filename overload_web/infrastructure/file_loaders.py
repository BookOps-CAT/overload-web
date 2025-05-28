""""""

from __future__ import annotations

import logging
import os
from typing import Protocol

from file_retriever import Client

logger = logging.getLogger(__name__)


class FileLoaderProtocol(Protocol):
    """
    Protocol for loading files ensuring local and remote files are implemented
    by all concrete sessions.
    """

    def get(self, file_name: str, dir: str) -> bytes: ...

    """Open a file and return the bytes object"""

    def list(self, dir: str) -> list[str]: ...

    """List all files in a directory"""


class LocalFileLoader(FileLoaderProtocol):
    def get(self, file_name: str, dir: str) -> bytes:
        """Open a local file"""
        file = b""
        with open(os.path.join(dir, file_name), "rb") as fh:
            file = fh.read()
        return file

    def list(self, dir: str) -> list[str]:
        """List all files local directory"""
        return [i for i in os.listdir(dir) if os.path.isfile(os.path.join(dir, i))]


class RemoteFileLoader(FileLoaderProtocol):
    def __init__(self) -> None:
        self.client = Client(
            name="nsdrop",
            username=os.environ["NSDROP_USER"],
            password=os.environ["NSDROP_PASS"],
            host=os.environ["NSDROP_HOST"],
            port=os.environ["NSDROP_PORT"],
        )

    def get(self, file_name: str, dir: str) -> bytes:
        """Open a file on remote storage"""
        file_info = self.client.get_file_info(file_name=file_name, remote_dir=dir)
        return self.client.get_file(file=file_info, remote_dir=dir).file_stream.read()

    def list(self, dir: str) -> list[str]:
        """List all files in a directory on remote storage"""
        return self.client.list_files(remote_dir=dir)
