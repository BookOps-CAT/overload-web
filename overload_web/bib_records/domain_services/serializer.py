"""Domain service for writing bib records to MARC binary.

Classes:

`BibSerializer`
    a domain service that outputs `DomainBib` objects to binary data.
"""

from __future__ import annotations

import io
import logging
from typing import BinaryIO

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BibSerializer:
    """Domain service for writing a `DomainBib` to MARC binary."""

    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Serialize a list of `bibs.DomainBib` objects into a binary MARC stream.

        Args:
            records: a list of records as `bibs.DomainBib` objects

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.__dict__}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data
