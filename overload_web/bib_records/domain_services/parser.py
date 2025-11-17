"""Parse MARC records"""

import io
import logging
from typing import BinaryIO

from overload_web.bib_records.domain import marc_protocols

logger = logging.getLogger(__name__)


class BibParser:
    def __init__(
        self,
        mapper: marc_protocols.BibMapper,
        vendor_identifier: marc_protocols.VendorIdentifier,
        reader: marc_protocols.BibReader,
        library: str,
    ) -> None:
        self.library = library
        self.mapper = mapper
        self.reader = reader
        self.vendor_identifier = vendor_identifier

    def parse(self, data: BinaryIO | bytes) -> list[marc_protocols.MapperVar]:
        records = []
        read_records: list = self.reader.read_records(data, self.library)
        for record in read_records:
            vendor_info = self.vendor_identifier.identify_vendor(
                record=record, library=self.library
            )
            mapped_bib = self.mapper.map_bib(record=record, info=vendor_info)
            logger.info(f"Vendor record parsed: {mapped_bib}")
            records.append(mapped_bib)
        return records

    def serialize(self, records: list[marc_protocols.MapperVar]) -> BinaryIO:
        """
        Serialize a list of `BibDTO` objects into a binary MARC stream.

        Args:
            records: a list of records as `BibDTO` objects

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.domain_bib.__dict__}")
            io_data.write(record.bib.as_marc())
        io_data.seek(0)
        return io_data
