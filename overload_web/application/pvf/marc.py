"""Application services for parsing MARC records during processing."""

from __future__ import annotations

import io
import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import models

logger = logging.getLogger(__name__)


class BibParser:
    def __init__(
        self,
        library: str,
        collection: str | None,
        record_type: str,
        bib_mapping: dict[str, Any],
        order_mapping: dict[str, Any],
        vendor_mapping: dict[str, Any],
    ) -> None:
        """
        Initialize `MarcParser` using a set of mapping rules and inputs.

        This class is an implementation of the `MarcParserPort` protocol.

        Args:
            library:
                the library whose records are being parsed
            collection:
                the collection to which the records belong
            record_type:
                the workflow two whom this record belongs
            bib_mapping:
                rules for mapping bookops_marc.Bib objects to domain objects
            order_mapping:
                rules for mapping bookops_marc.Order objects to domain objects
            vendor_mapping:
                rules for identifying the vendor to whom a record belongs
        """
        self.library = library
        self.collection = collection
        self.record_type = record_type
        self.bib_mapping = bib_mapping
        self.order_mapping = order_mapping
        self.vendor_mapping = vendor_mapping

    def combine_marc_files(
        self, data: list[bytes], handler: ports.MarcParserPort
    ) -> bytes:
        """Combine multiple bytes objects (ie. MARC files) into one for processing."""
        records = []
        for batch in data:
            reader = handler.get_reader(batch, library=self.library)
            for record in reader:
                records.append(record)
        io_data = io.BytesIO()
        for record in records:
            io_data.write(record.as_marc())
        io_data.seek(0)
        return io_data.getvalue()

    def parse_record(
        self,
        bib_dict: dict[str, Any],
        order_data: list[dict[str, Any]],
        vendor_info: dict[str, Any] | None,
        vendor: str | None,
        collection: str | None,
        binary_data: bytes,
    ) -> models.DomainBib:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
        bib_dict["orders"] = [models.Order(**i) for i in order_data]
        bib_dict["binary_data"] = binary_data
        bib_dict["record_type"] = self.record_type
        if isinstance(vendor_info, dict):
            bib_dict["vendor_info"] = models.VendorInfo(**vendor_info)
        else:
            bib_dict["vendor"] = vendor
        if not collection:
            bib_dict["collection"] = self.collection
        bib = models.DomainBib(**bib_dict)
        return bib

    def parse_marc_data(
        self, data: bytes, handler: ports.MarcParserPort, vendor: str | None = "UNKNOWN"
    ) -> list[models.DomainBib]:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
        vendor_info: dict[str, Any] | None
        parsed = []
        reader = handler.get_reader(data, library=self.library)
        for record in reader:
            bib_dict = handler.map_bib_data(obj=record, mapping=self.bib_mapping)
            order_data = [
                handler.map_order_data(obj=i, mapping=self.order_mapping)
                for i in record.orders
            ]
            if self.record_type == "cat":
                vendor_info = handler.identify_vendor(
                    obj=record, mapping=self.vendor_mapping
                )
            else:
                vendor_info = None
            parsed_bib = self.parse_record(
                bib_dict=bib_dict,
                order_data=order_data,
                binary_data=record.as_marc(),
                vendor_info=vendor_info,
                vendor=vendor,
                collection=bib_dict.get("collection"),
            )
            logger.info(f"Vendor record parsed: {parsed_bib}")
            parsed.append(parsed_bib)
        return parsed
