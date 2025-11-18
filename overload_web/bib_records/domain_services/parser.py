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
        reader: marc_protocols.MarcReaderProtocol,
        vendor_identifier: marc_protocols.VendorIdentifier,
    ) -> None:
        self.mapper = mapper
        self.reader = reader
        self.vendor_identifier = vendor_identifier

    def parse(self, data: BinaryIO | bytes) -> list[marc_protocols.BibDTOProtocol]:
        mapped_bibs = []
        records: list = self.reader.read_records(data)
        for record in records:
            vendor_info = self.vendor_identifier.identify_vendor(record=record)
            mapped_bib = self.mapper.map_bib(record=record, info=vendor_info)
            logger.info(f"Vendor record parsed: {mapped_bib}")
            mapped_bibs.append(mapped_bib)
        return mapped_bibs

    def serialize(self, records: list[marc_protocols.BibDTOProtocol]) -> BinaryIO:
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
