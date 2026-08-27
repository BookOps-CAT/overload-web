"""Application service commands for file handling."""

import logging
import uuid
from typing import Any, Sequence

from overload_web.application import ports
from overload_web.domain.shared import files

logger = logging.getLogger(__name__)


class ListVendorFiles:
    @staticmethod
    def execute(dir: str, loader: ports.FileLoader) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory whose files to list as a string.
            loader: Concrete implementation of `FileLoader` protocol
        Returns:
            a list of filenames contained within the given directory as strings.
        """
        files = loader.list(dir=dir)
        return files


class LoadVendorFile:
    @staticmethod
    def execute(name: str, dir: str, loader: ports.FileLoader) -> files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located as a string.
            loader: Concrete implementation of `FileLoader` protocol.

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = loader.load(name=name, dir=dir)
        return files.VendorFile(file_name=name, content=file)


class WriteFile:
    @staticmethod
    def execute(file: bytes, file_name: str, dir: str, writer: ports.FileWriter) -> str:
        """
        Write a file to a directory.

        Args:
            file: The file content to write as a bytes object.
            file_name: The name of the file as a string.
            dir: The directory where the file should be written as a string.
            writer: Concrete implementation of `FileWriter` protocol.

        Returns:
            the directory and filename where the file was written.
        """
        out_file = writer.write(file=file, file_name=file_name, dir=dir)
        return out_file


class UploadFileToWorkflow:
    @staticmethod
    def execute(
        workflow_id: str,
        filename: str,
        content: bytes,
        source: str,
        storage: ports.FileStorage,
        repo: ports.SqlRepositoryProtocol,
    ) -> Sequence[dict[str, Any]]:
        """
        Uploads a file for a workflow.


        Args:
            workflow_id:
                The id of the workflow to which the file belongs.
            filename:
                The name of the file as a str.
            content:
                The content of the file as a bytes object
            source:
                The source of the file (ie. either `local` or `ftp`)
            storage:
                Concrete implementation of the `FileStorage` for
                handling vendor files.
            repo:
                Concrete implementation of the `SqlRepositoryProtocol` for
                handling vendor files.

        Returns:
            The list of files for workflow as a list of `VendorFile` objects.
        """
        file_id = str(uuid.uuid4())
        reference = storage.save(id=file_id, filename=filename, content=content)
        file = files.IncomingFile(
            id=file_id,
            workflow_id=workflow_id,
            filename=filename,
            source=source,
            reference=reference,
        )
        repo.save(file)
        logger.info(f"File added to workflow {workflow_id}: {file}.")
        return repo.list_by_id(workflow_id)


class LoadAllWorkflowFiles:
    @staticmethod
    def execute(
        workflow_id: str, storage: ports.FileStorage, repo: ports.SqlRepositoryProtocol
    ) -> list[files.VendorFile]:
        """
        Loads all files for a workflow.


        Args:
            workflow_id:
                The id of the workflow whose files are to be loaded.
            repo:
                Concrete implementation of the `SqlRepositoryProtocol` for
                handling vendor files.
            storage:
                Concrete implementation of the `FileStorage` for
                handling vendor files.
        Returns:
            The list of files for workflow as a list of `VendorFile` objects.
        """
        file_list = repo.list_by_id(workflow_id)
        vendor_files = [
            files.VendorFile(
                file_name=i["filename"], content=storage.load(i["reference"])
            )
            for i in file_list
        ]
        logger.info(f"Loading all files for workflow {workflow_id}: {vendor_files}.")
        return vendor_files


class DeleteFileFromWorkflow:
    @staticmethod
    def execute(
        id: str, workflow_id: str, repo: ports.SqlRepositoryProtocol
    ) -> Sequence[dict[str, Any]]:
        """
        Delete an incoming file from the workflow's list of files.


        Args:
            id:
                The id to the file to remove from the workflow as a str.
            workflow_id:
                The id of the workflow to which the file belongs.
            repo:
                Concrete implementation of the `SqlRepositoryProtocol` for
                handling vendor files.

        Returns:
            The list of files remaining for the workflow as a list of dictionaries.
        """
        repo.delete(id)
        return repo.list_by_id(workflow_id)
