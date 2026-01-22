"""Domain service for serializing bib records to binary data."""

from __future__ import annotations

import io
import logging
from typing import BinaryIO

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)


class OrderLevelBibSerializer:
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


class FullLevelBibSerializer:
    def serialize(
        self,
        record_batches: dict[str, list[bibs.DomainBib]],
    ) -> dict[str, BinaryIO]:
        """
        Serialize `DomainBib` objects into a binary MARC stream and split into
        appropriate file streams based on analysis.

        Args:
            record_batches:
                A dictionary containing list of parsed bibliographic records
                as `DomainBib` objects organized by the files they should
                be written to.

        Returns:
            A dictionary containing the file type and an in-memory file stream
            for each type of file to be written.
        """
        deduped_record_data = io.BytesIO()
        dupe_record_data = io.BytesIO()
        new_record_data = io.BytesIO()
        for file, records in record_batches.items():
            for record in records:
                logger.info(f"Writing MARC binary for record: {record}")
                if file == "DEDUPED":
                    deduped_record_data.write(record.binary_data)
                elif file == "NEW":
                    new_record_data.write(record.binary_data)
                else:
                    dupe_record_data.write(record.binary_data)
        deduped_record_data.seek(0)
        dupe_record_data.seek(0)
        new_record_data.seek(0)
        return {
            "DEDUPED": deduped_record_data,
            "DUP": dupe_record_data,
            "NEW": new_record_data,
        }
