import logging

from overload_web.application import ports
from overload_web.domain.models import files

logger = logging.getLogger(__name__)


class ListVendorFiles:
    @staticmethod
    def execute(dir: str, loader: ports.FileLoader) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory whose files to list.
            loader: concrete implementation of `FileLoader` protocol
        Returns:
            a list of filenames contained within the given directory as strings.
        """
        files = loader.list(dir=dir)
        logger.info(f"Files in {dir}: {files}")
        return files


class LoadVendorFile:
    @staticmethod
    def execute(name: str, dir: str, loader: ports.FileLoader) -> files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located.
            loader: concrete implementation of `FileLoader` protocol

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = loader.load(name=name, dir=dir)
        logger.info(f"File loaded: {name}")
        return file


class WriteFile:
    @staticmethod
    def execute(file: files.VendorFile, dir: str, writer: ports.FileWriter) -> str:
        """
        Write a file to a directory.

        Args:
            file: The file to write as a `files.VendorFile` object.
            dir: The directory where the file should be written.
            writer: concrete implementation of `FileWriter` protocol

        Returns:
            the directory and filename where the file was written.
        """
        out_file = writer.write(file=file, dir=dir)
        logger.info(f"Writing file to directory: {dir}/{out_file}")
        return out_file
