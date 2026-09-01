"""Adapter module defining classes used to read MARC records.

Protocols:

`DomainBibProtocol`
    A protocol that defines a `DomainBib` used in this application. Defined in order
    to not have infrastructure layer dependent on domain layer.

Classes:

`MarcEngineConfig`
    Configuration data used to determine MARC record processing. Loaded from a .json
    file and input via an html form in the presentation layer.
`MarcReaderWriter`
    Read binary MARC data using `bookops_marc`.
"""

from __future__ import annotations

import io
import logging
from typing import BinaryIO, Protocol

from bookops_marc import SierraBibReader

logger = logging.getLogger(__name__)


class DomainBibProtocol(Protocol):
    library: str
    binary_data: bytes


class MarcReaderWriter:
    """Interacts with binary MARC data using `bookops_marc`."""

    def __init__(self, library: str) -> None:
        """
        Initialize `MarcReaderWriter` for a given library.

        This class is a concrete implementation of the `ReaderWriter` protocol.

        Args:
            library: the library whose records are being read/written
        """
        self.library = library

    def get_reader(self, data: bytes | BinaryIO) -> SierraBibReader:
        """Instantiate a `SierraBibReader` to read MARC binary data."""
        return SierraBibReader(data, library=self.library)

    def write(self, records: list[DomainBibProtocol]) -> bytes:
        """
        Serialize `DomainBib` objects into a binary MARC stream.

        Args:
            records:
                A list `DomainBib` objects.

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        out = io_data.getvalue()
        return out
