"""Application service commands for file handling."""

import logging

from overload_web.domain.pvf import files, ports

logger = logging.getLogger(__name__)


class ListVendorFiles:
    """List files in a directory."""

    @staticmethod
    def execute(dir: str, retriever: ports.FileRetriever) -> list[str]:
        """Execute `ListVendorFiles` command.

        Args:
            dir: The directory whose files to list as a string.
            retriever: Concrete implementation of `FileRetriever` protocol
        Returns:
            a list of filenames contained within the given directory as strings.

        """
        files = retriever.list(dir=dir)
        return files


class DownloadVendorFile:
    """Load a file from a directory."""

    @staticmethod
    def execute(
        name: str, dir: str, retriever: ports.FileRetriever
    ) -> files.VendorFile:
        """Execute `DownloadVendorFile` command.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located as a string.
            retriever: Concrete implementation of `FileRetriever` protocol.

        Returns:
            The loaded file as a `files.VendorFile` object.

        """
        file = retriever.download(name=name, dir=dir)
        return files.VendorFile(file_name=name, content=file)
