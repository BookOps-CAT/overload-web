"""Application services for interacting with DomainBib objects during processing."""

from __future__ import annotations

import io
import logging
from collections import Counter
from typing import Any, Iterator

from overload_web.application import ports
from overload_web.domain.pvf import bibs, cataloging_rules

logger = logging.getLogger(__name__)


class BibDeduplicator:
    @staticmethod
    def deduplicate(
        records: list[bibs.DomainBib], engine: ports.MarcUpdateEnginePort
    ) -> dict[str, list[bibs.DomainBib]]:
        """Review and deduplicate a batch of processed full-level MARC records."""
        merge: list[bibs.DomainBib] = []
        new: list[bibs.DomainBib] = []
        deduped: list[bibs.DomainBib] = []
        for record in records:
            if record.action and record.action == "attach":
                merge.append(record)
            else:
                new.append(record)
        if not new:
            return {"NEW": merge, "DUP": new, "DEDUPED": deduped}
        logger.debug("Deduping new records")
        new_record_counter = Counter([i.control_number for i in new])
        dupe_recs = [i for i, count in new_record_counter.items() if count > 1]
        if not dupe_recs:
            logger.debug("No duplicates found in file.")
            return {"NEW": merge, "DUP": new, "DEDUPED": deduped}
        logger.info("Discovered duplicate records in processed file")

        processed_dupes = []
        for record in new:
            if record.control_number not in dupe_recs:
                deduped.append(record)
            if record.control_number in processed_dupes:
                continue
            all_dupes = [i for i in new if i.control_number == record.control_number]
            base_rec = engine.create_bib_from_domain(record=all_dupes[0])
            if base_rec.library == "bpl" and base_rec.overdrive_number is None:
                tag = "960"
                ind2 = " "
            else:
                tag = "949"
                ind2 = "1"
            all_items = []
            for dupe in all_dupes[1:]:
                dupe_bib = engine.create_bib_from_domain(record=dupe)
                all_items.extend(dupe_bib.get_fields(tag))
            for item in all_items:
                if item.indicator1 == " " and item.indicator2 == ind2:
                    base_rec.add_ordered_field(item)
            record.binary_data = base_rec.as_marc()
            processed_dupes.append(record.control_number)
            deduped.append(record)
        return {"NEW": merge, "DUP": new, "DEDUPED": deduped}


class BibReader:
    @staticmethod
    def read_marc_data(data: bytes, marc_reader: ports.ReaderWriter) -> Iterator:
        """Parse MARC binary into an iterator."""
        return marc_reader.get_reader(data)


class BibParser:
    @staticmethod
    def parse_marc_data(
        reader: Iterator,
        parser: ports.MarcParsingEnginePort,
        vendor: str | None = "UNKNOWN",
    ) -> list[bibs.DomainBib]:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
        parsed = []
        for record in reader:
            bib_dict = parser.map_bib_data(obj=record)
            order_data = [parser.map_order_data(obj=i) for i in record.orders]
            bib_dict["orders"] = [bibs.Order(**i) for i in order_data]
            bib_dict["binary_data"] = record.as_marc()
            bib_dict["record_type"] = parser.record_type
            if parser.record_type == "cat":
                vendor_info = parser.identify_vendor(record=record)
                bib_dict["vendor_info"] = bibs.VendorInfo(**vendor_info)
            else:
                bib_dict["vendor"] = vendor
            if not bib_dict.get("collection"):
                bib_dict["collection"] = parser.collection
            bib = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {bib}")
            parsed.append(bib)
        return parsed


class BibUpdater:
    @staticmethod
    def get_acq_updates(
        record: bibs.DomainBib, config: Any, template_data: dict[str, Any]
    ) -> list:
        """Get list of MARC fields to update in processed acq bib record"""
        return cataloging_rules.AcquisitionUpdates.field_list(
            record=record, context=config, template_data=template_data
        )

    @staticmethod
    def get_cat_updates(record: bibs.DomainBib, config: Any) -> list:
        """Get list of MARC fields to update in processed full-level bib record"""
        return cataloging_rules.CatalogingUpdates.field_list(
            record=record, context=config
        )

    @staticmethod
    def get_sel_updates(
        record: bibs.DomainBib,
        config: Any,
        command_tag: Any,
        template_data: dict[str, Any],
    ) -> list:
        """Update and add MARC fields to sel bib record"""
        return cataloging_rules.SelectionUpdates.field_list(
            record=record,
            context=config,
            template_data=template_data,
            command_tag=command_tag,
        )

    @staticmethod
    def update_record(
        record: bibs.DomainBib, engine: ports.MarcUpdateEnginePort, updates: list
    ) -> None:
        """Update and add MARC fields to bib record"""
        bib = engine.create_bib_from_domain(record=record)
        engine.update_fields(field_updates=updates, bib=bib)
        bib.leader = cataloging_rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()


class MarcFileMerger:
    @staticmethod
    def combine_marc_files(data: list[bytes], marc_reader: ports.ReaderWriter) -> bytes:
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


class BarcodeValidator:
    @staticmethod
    def validate_unique(barcodes: list[str]) -> None:
        """Confirm barcodes in a file are all unique."""
        barcode_counter = Counter(barcodes)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise ValueError(f"Duplicate barcodes found in file: {dupe_barcodes}")

    @staticmethod
    def validate_preserved(
        processed_barcodes: list[str], original_barcodes: list[str]
    ) -> list[str]:
        """Confirm barcodes extracted from a file are present in processed records"""
        missing_barcodes = set()
        for barcode in original_barcodes:
            if barcode not in processed_barcodes:
                missing_barcodes.add(barcode)
        valid = sorted(original_barcodes) == sorted(processed_barcodes)
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
        return list(missing_barcodes)
