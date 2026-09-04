"""Application services for parsing MARC records during processing."""

from __future__ import annotations

import io
import logging
from collections import Counter

from overload_web.application import ports
from overload_web.domain.pvf import models
from overload_web.domain.shared import fields

logger = logging.getLogger(__name__)


class BibDeduplicator:
    @staticmethod
    def deduplicate(
        records: list[models.DomainBib], handler: ports.MarcUpdateHandlerPort
    ) -> dict[str, list[models.DomainBib]]:
        """Review and deduplicate a batch of processed full-level MARC records."""
        out: dict[str, list[models.DomainBib]] = {"NEW": [], "DUP": [], "DEDUPED": []}
        for record in records:
            if record.action and record.action == "attach":
                out["NEW"].append(record)
            else:
                out["DUP"].append(record)
        if not out["DUP"]:
            return out
        logger.debug("Deduping new records")
        new_record_counter = Counter([i.control_number for i in out["DUP"]])
        dupe_recs = [i for i, count in new_record_counter.items() if count > 1]
        if not dupe_recs:
            logger.debug("No duplicates found in file.")
            return out
        logger.info("Discovered duplicate records in processed file")
        processed_dupes = []
        for record in out["DUP"]:
            if record.control_number not in dupe_recs:
                out["DEDUPED"].append(record)
            if record.control_number in processed_dupes:
                continue
            all_dupes = [
                i for i in out["DUP"] if i.control_number == record.control_number
            ]
            base_rec = handler.create_bib_from_domain(record=all_dupes[0])
            tag = "949"
            ind2 = "1"
            if base_rec.library == "bpl" and base_rec.overdrive_number is None:
                tag = "960"
                ind2 = " "
            all_items = []
            for dupe in all_dupes[1:]:
                dupe_bib = handler.create_bib_from_domain(record=dupe)
                all_items.extend(dupe_bib.get_fields(tag))
            for item in all_items:
                if item.indicator1 == " " and item.indicator2 == ind2:
                    base_rec.add_ordered_field(item)
            record.binary_data = base_rec.as_marc()
            processed_dupes.append(record.control_number)
            #     all_items.extend([i for i in dupe.parsed_fields if i.tag == tag])
            # new_items = marc_rules.FieldRules.add_item_fields(
            #     items=all_items, ind2=ind2, tag=tag
            # )
            # handler.update_fields(new_items, bib=base_rec)
            # record.binary_data = base_rec.as_marc()
            # processed_dupes.append(record.control_number)
            out["DEDUPED"].append(record)
        return out


class BibParser:
    @staticmethod
    def combine_marc_files(
        data: list[bytes], marc_handler: ports.MarcParsingHandlerPort
    ) -> bytes:
        """Combine multiple bytes objects (ie. MARC files) into one for processing."""
        records = []
        for batch in data:
            reader = marc_handler.reader.get_reader(batch)
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
