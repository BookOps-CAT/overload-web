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
import logging
import os
from pathlib import Path
from typing import Any, Sequence

from file_retriever import Client, File
from sqlmodel import Field, Session, SQLModel, select

logger = logging.getLogger(__name__)


class LocalFileStorage:
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


class LocalFileLoader:
    """
    Loads files from the local filesystem.

    This class implements the `FileLoader` protocol by listing and loading file
    contents from a specific directory on a local computer.
    """

    def list(self, dir: str) -> list[str]:
        """List available files in a local directory."""
        files = os.listdir(dir)
        logger.info(f"Files in {dir}: {files}")
        return files

    def load(self, name: str, dir: str) -> bytes:
        """Load a file from a local directory."""
        with open(os.path.join(dir, name), "rb") as fh:
            file = fh.read()
        logger.info(f"File loaded: {name}")
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
        logger.info(f"Writing file to directory: {path}")
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
        files = self.client.list_files(remote_dir=dir)
        logger.info(f"Files in {dir}: {files}")
        return files

    def load(self, name: str, dir: str) -> bytes:
        """Load a file from a remote directory."""
        file_info = self.client.get_file_info(file_name=name, remote_dir=dir)
        file = self.client.get_file(file=file_info, remote_dir=dir)
        file.file_stream.seek(0)
        logger.info(f"File loaded: {name}")
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
        logger.info(f"Writing file to directory: {dir}/{out_file}")
        return getattr(out_file, "file_name", file_name)


class IncomingFileModel(SQLModel, table=True):
    __tablename__ = "incoming_files"
    id: str = Field(default=None, primary_key=True, index=True)
    filename: str = Field(nullable=False)
    workflow_id: str = Field(nullable=False, index=True)
    source: str = Field(nullable=False)
    reference: str = Field(nullable=False)


class IncomingFileRepository:
    def __init__(self, session: Session):
        self.session = session

    def delete(self, id: str | int) -> None:
        """
        Delete an `IncomingFileModel` object from the workflow's list of files.

        Args:
            id: the ID of the file to delete.

        Returns:
            None
        """
        statement = select(IncomingFileModel).where(IncomingFileModel.id == id)
        self.session.exec(statement)

    def get(self, id: str | int) -> dict[str, Any] | None:
        """
        Retrieve an `IncomingFileModel` object by its ID.

        Args:
            id: the primary key of the `IncomingFileModel`.

        Returns:
            a `IncomingFileModel` instance as a dictionary or `None` if not found.
        """
        file = self.session.get(IncomingFileModel, id)
        return file.model_dump() if file else None

    def list_by_id(self, id: str | int) -> Sequence[dict[str, Any]]:
        """
        Retrieve all `IncomingFileModel` objects in the database.

        Args:
            id: the `workflow_id` whose files to retrieve.

        Returns:
            a sequence of `IncomingFileModel` objects.
        """
        statement = select(IncomingFileModel).where(IncomingFileModel.workflow_id == id)
        results = self.session.exec(statement)
        all_files = results.all()
        return [i.model_dump() for i in all_files]

    def save(self, obj: IncomingFileModel) -> dict[str, Any]:
        """
        Adds a new `IncomingFileModel` to the database.

        Args:
            obj: the `IncomingFileModel` object to save.

        Returns:
            The `IncomingFileModel` data as a dictionary.
        """
        valid_obj = IncomingFileModel.model_validate(obj, from_attributes=True)
        self.session.add(valid_obj)
        self.session.commit()
        self.session.refresh(valid_obj)
        return valid_obj.model_dump()
