"""Domain service for serializing bib records to binary data."""

from __future__ import annotations

import io
import logging
from typing import BinaryIO

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class BibSerializer:
    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Serialize `DomainBib` objects into a binary MARC stream.

        Args:
            records:
                A list of parsed bibliographic records as `DomainBib` objects.

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data
