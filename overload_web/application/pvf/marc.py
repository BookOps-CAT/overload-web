"""Application services for interacting with DomainBib objects during processing."""

from __future__ import annotations

import io
import logging
from collections import Counter
from typing import Any

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


class BibParser:
    @staticmethod
    def parse_marc_data(
        data: bytes, parser: ports.MarcParsingEnginePort, vendor: str | None = "UNKNOWN"
    ) -> list[bibs.DomainBib]:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
        parsed = []
        reader = parser.get_reader(data)
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
            bib_dict["parsed_fields"] = [
                bibs.ParsedField(**i) for i in bib_dict["parsed_fields"]
            ]
            bib = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {bib}")
            parsed.append(bib)
        return parsed


class BibUpdater:
    def __init__(
        self,
        bib_id_tag: str,
        collection: str | None,
        default_loc: str | None,
        library: str,
        order_mapping: dict[str, Any],
        record_type: str,
    ) -> None:
        self.bib_id_tag = bib_id_tag
        self.collection = collection
        self.default_loc = default_loc
        self.library = library
        self.order_mapping = order_mapping
        self.record_type = record_type

    def get_acq_updates(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> list[cataloging_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to update in processed acq bib record"""
        return cataloging_rules.AcquisitionUpdates.field_list(
            record=record,
            bib_id_tag=self.bib_id_tag,
            library=self.library,
            order_mapping=self.order_mapping,
            template_data=template_data,
        )

    def get_cat_updates(
        self, record: bibs.DomainBib
    ) -> list[cataloging_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to update in processed full-level bib record"""
        return cataloging_rules.CatalogingUpdates.field_list(
            record=record, bib_id_tag=self.bib_id_tag, library=self.library
        )

    def get_sel_updates(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> list[cataloging_rules.MarcFieldUpdateValues]:
        """Update and add MARC fields to sel bib record"""
        return cataloging_rules.SelectionUpdates.field_list(
            record=record,
            bib_id_tag=self.bib_id_tag,
            default_loc=self.default_loc,
            library=self.library,
            order_mapping=self.order_mapping,
            template_data=template_data,
        )

    def update_record(
        self,
        record: bibs.DomainBib,
        engine: ports.MarcUpdateEnginePort,
        updates: list[cataloging_rules.MarcFieldUpdateValues],
    ) -> None:
        """Update and add MARC fields to bib record"""
        bib = engine.create_bib_from_domain(record=record)
        engine.update_fields(field_updates=updates, bib=bib)
        bib.leader = cataloging_rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()


class MarcFileMerger:
    @staticmethod
    def combine_marc_files(
        data: list[bytes], marc_reader: ports.MarcParsingEnginePort
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
