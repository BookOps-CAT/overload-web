"""Application services for parsing MARC records during processing."""

from __future__ import annotations

import io
import logging

from overload_web.application import ports
from overload_web.domain.pvf import models
from overload_web.domain.shared import fields

logger = logging.getLogger(__name__)


class BibParser:
    @staticmethod
    def combine_marc_files(
        data: list[bytes], marc_reader: ports.MarcReaderPort
    ) -> bytes:
        """Combine multiple bytes objects (ie. MARC files) into one for processing."""
        records = []
        for batch in data:
            reader = marc_reader.get_reader(batch)
            for record in reader:
                records.append(record)
        io_data = io.BytesIO()
        for record in records:
            io_data.write(record.as_marc())
        io_data.seek(0)
        return io_data.getvalue()

    @staticmethod
    def parse_marc_data(
        data: bytes,
        parser: ports.MarcParsingHandlerPort,
        vendor: str | None = "UNKNOWN",
    ) -> list[models.DomainBib]:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
        parsed = []
        reader = parser.reader.get_reader(data)
        for record in reader:
            bib_dict = parser.map_bib_data(obj=record)
            order_data = [parser.map_order_data(obj=i) for i in record.orders]
            bib_dict["orders"] = [models.Order(**i) for i in order_data]
            bib_dict["binary_data"] = record.as_marc()
            bib_dict["record_type"] = parser.record_type
            if parser.record_type == "cat":
                vendor_info = parser.identify_vendor(record=record)
                bib_dict["vendor_info"] = models.VendorInfo(**vendor_info)
            else:
                bib_dict["vendor"] = vendor
            if not bib_dict.get("collection"):
                bib_dict["collection"] = parser.collection
            bib_dict["parsed_fields"] = [
                fields.ParsedField(**i) for i in bib_dict["parsed_fields"]
            ]
            bib = models.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {bib}")
            parsed.append(bib)
        return parsed
