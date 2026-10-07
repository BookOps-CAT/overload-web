"""
Local and FTP/SFTP file I/O implementations for Overload.

This module contains classes to load files from and write files to local
directories and remote FTP/SFTP servers. The classes that interact with remote
directories within this module use the BookOps/file-retriever library.
The classes within this module are concrete implementations of the `FileRetriever`,
`FileStorage` and `FileWriter` protocols within the domain model.
"""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path

from file_retriever import Client

from overload_web.domain.pvf import aggregate, ports

logger = logging.getLogger(__name__)


class LocalFileStorage(ports.FileStorage):
    def __init__(self, base_path: str = "temp/uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"Local file storage location: {self.base_path}")

    def save(self, id: str, filename: str, content: bytes) -> str:
        path = self.base_path / f"{id}_{filename}"

        with open(path, "wb") as f:
            f.write(content)

        return str(path)

    def load(self, reference: str) -> bytes:
        with open(reference, "rb") as fh:
            file = fh.read()
        return file

    def save_intermediate_records(
        self, id: str, job: aggregate.AbstractProcessingJob
    ) -> None:
        """Serializes the intermediate domain objects to disk."""
        file_path = self.base_path / f"{id}_state.pkl"
        with open(file_path, "wb") as f:
            pickle.dump(job, f)

    def load_intermediate_records(self, id: str) -> aggregate.AbstractProcessingJob:
        """Deserializes the domain objects back into memory."""
        file_path = self.base_path / f"{id}_state.pkl"

        if not file_path.exists():
            raise FileNotFoundError(f"No intermediate state found for {id}.")
        with open(file_path, "rb") as f:
            return pickle.load(f)


class LocalFileRetriever(ports.FileRetriever):
    """
    Loads files from the local filesystem.

    This class implements the `FileRetriever` protocol by listing and loading file
    contents from a specific directory on a local computer.
    """

    def download(self, dir: str, name: str) -> bytes:
        """Load a file from a local directory."""
        with open(os.path.join(dir, name), "rb") as fh:
            file = fh.read()
        logger.info(f"File loaded: {name}")
        return file

    def list(self, dir: str) -> list[str]:
        """List available files in a local directory."""
        files = os.listdir(dir)
        logger.info(f"Files in {dir}: {files}")
        return files


class LocalFileWriter(ports.FileWriter):
    """
    Writes files to the local filesystem.

    This class implements the `FileWriter` protocol by writing binary content
    to files within a specific directory on a local computer.
    """

    def write(self, dir: str, file: bytes, file_name: str) -> str:
        """Write a file to a local directory."""
        path = os.path.join(dir, file_name)
        with open(path, "wb") as f:
            f.write(file)
        logger.info(f"Writing file to directory: {path}")
        return path


class SFTPFileRetriever(ports.FileRetriever):
    """
    Loads files from a remote FTP/SFTP server.

    Implements the `FileRetriever` protocol using the file-retriever library
    to connect to an FTP/SFTP server.
    """

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(self, dir: str) -> list[str]:
        """List files in a remote directory."""
        files = self.client.list_files(remote_dir=dir)
        logger.info(f"Files in {dir}: {files}")
        return files

    def download(self, dir: str, name: str) -> bytes:
        """Load a file from a remote directory."""
        file_info = self.client.get_file_info(file_name=name, remote_dir=dir)
        file = self.client.get_file(file=file_info, remote_dir=dir)
        file.file_stream.seek(0)
        logger.info(f"File loaded: {name}")
        return file.file_stream.read()

    @classmethod
    def create_retriever_for_vendor(cls, vendor: str) -> SFTPFileRetriever:
        """Create an `SFTPFileRetriever` for a specific vendor based on envars."""
        client = Client(
            name=vendor.upper(),
            username=os.environ[f"{vendor.upper()}_USER"],
            password=os.environ[f"{vendor.upper()}_PASSWORD"],
            host=os.environ[f"{vendor.upper()}_HOST"],
            port=os.environ[f"{vendor.upper()}_PORT"],
        )
        return SFTPFileRetriever(client=client)
