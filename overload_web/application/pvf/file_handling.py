"""Application service commands for file handling."""

import logging
import uuid
from typing import Any, Sequence

from overload_web.domain.pvf import files, ports

logger = logging.getLogger(__name__)


class ListVendorFiles:
    @staticmethod
    def execute(dir: str, retriever: ports.FileRetriever) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory whose files to list as a string.
            retriever: Concrete implementation of `FileRetriever` protocol
        Returns:
            a list of filenames contained within the given directory as strings.
        """
        files = retriever.list(dir=dir)
        return files


class DownloadRemoteFile:
    @staticmethod
    def execute(
        name: str, dir: str, retriever: ports.FileRetriever
    ) -> files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located as a string.
            retriever: Concrete implementation of `FileRetriever` protocol.

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = retriever.download(name=name, dir=dir)
        return files.VendorFile(file_name=name, content=file)


class UploadFileToWorkflow:
    """Saves incoming vendor file bytes and ensures a DRAFT WorkflowJob exists."""

    @staticmethod
    def execute(
        content: bytes,
        filename: str,
        source: str,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
    ) -> Sequence[dict[str, Any]]:
        """Saves file data to storage and persists database metadata within a UoW.

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
            The saved IncomingFile domain entity.
        """
        file_id = str(uuid.uuid4())
        reference = storage.save(id=file_id, filename=filename, content=content)
        with uow:
            file = files.IncomingFile(
                id=file_id,
                workflow_id=workflow_id,
                filename=filename,
                source=source,
                reference=reference,
            )
            uow.incoming_files.save(file)
            logger.info(f"File added to workflow {workflow_id}: {file}.")

            uow.commit()

        return uow.incoming_files.list_by_id(workflow_id)


class DeleteFileFromWorkflow:
    @staticmethod
    def execute(
        id: str, workflow_id: str, uow: ports.UnitOfWorkProtocol
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
        with uow:
            uow.incoming_files.delete(id)
            files = uow.incoming_files.list_by_id(workflow_id)
            return files
