from __future__ import annotations

import io
import itertools
import logging
from collections import Counter
from typing import Any

from overload_web.application import ports
from overload_web.domain.errors import OverloadError
from overload_web.domain.models import bibs, rules

logger = logging.getLogger(__name__)


class BarcodeExtractor:
    @staticmethod
    def extract_barcodes(records: list[bibs.DomainBib]) -> list[str]:
        """Extract all barcodes from a list of `DomainBib` objects"""
        return list(itertools.chain.from_iterable([i.barcodes for i in records]))


class BarcodeValidator:
    @staticmethod
    def ensure_preserved(
        record_batches: dict[str, list[bibs.DomainBib]], barcodes: list[str]
    ) -> list[str]:
        valid = True
        barcodes_from_batches = list(
            itertools.chain.from_iterable(
                i.barcodes for j in record_batches.values() for i in j
            )
        )
        missing_barcodes = set()
        for barcode in barcodes:
            if barcode not in barcodes_from_batches:
                valid = False
                missing_barcodes.add(barcode)
        valid = sorted(barcodes) == sorted(barcodes_from_batches)
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
        return list(missing_barcodes)

    @staticmethod
    def ensure_unique(bibs: list[bibs.DomainBib]) -> None:
        barcodes = list(itertools.chain.from_iterable([i.barcodes for i in bibs]))
        barcode_counter = Counter(barcodes)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise OverloadError(f"Duplicate barcodes found in file: {dupe_barcodes}")


class BibParser:
    @staticmethod
    def parse_marc_data(
        data: bytes, engine: ports.MarcEnginePort, vendor: str | None = "UNKNOWN"
    ) -> list[bibs.DomainBib]:
        reader = engine.get_reader(data)
        parsed = []
        for record in reader:
            bib_dict = engine.map_data(obj=record, rules=engine.bib_rules)
            order_data = [
                engine.map_data(obj=i, rules=engine.order_rules) for i in record.orders
            ]
            bib_dict["orders"] = [bibs.Order(**i) for i in order_data]
            bib_dict["binary_data"] = record.as_marc()
            bib_dict["record_type"] = engine.record_type
            if engine.record_type == "cat":
                bib_dict["vendor_info"] = bibs.VendorInfo(
                    **engine.identify_vendor(record=record, rules=engine.vendor_rules)
                )
            else:
                bib_dict["vendor"] = vendor
            if not bib_dict["collection"]:
                bib_dict["collection"] = engine.collection
            bib = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {bib}")
            parsed.append(bib)
        return parsed


class BibUpdater:
    @staticmethod
    def update_record(
        record: bibs.DomainBib, engine: ports.MarcEnginePort, **kwargs: Any
    ) -> None:
        template_data = kwargs.get("template_data", {})
        record.apply_order_template(template_data)
        bib = engine.create_bib_from_domain(record=record)

        updates = rules.VendorRules.fields_to_update(
            record=record,
            format=template_data.get("format"),
            call_no=engine.get_value_of_field(tag="091", bib=bib),
            command_tag=engine.get_command_tag_field(bib),
            context=engine._config,
        )
        engine.update_fields(field_updates=updates, bib=bib)
        bib.leader = rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()


class BibSerializer:
    @staticmethod
    def write(records: list[bibs.DomainBib]) -> io.BytesIO:
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


class Deduplicator:
    @staticmethod
    def deduplicate(
        records: list[bibs.DomainBib], engine: ports.MarcEnginePort
    ) -> dict[str, list[bibs.DomainBib]]:
        merge: list[bibs.DomainBib] = []
        new: list[bibs.DomainBib] = []
        deduped: list[bibs.DomainBib] = []
        for record in records:
            if record.analysis and record.analysis.action == bibs.CatalogAction.ATTACH:
                merge.append(record)
            else:
                new.append(record)
        if not new:
            return {"DUP": merge, "NEW": new, "DEDUPED": deduped}
        logger.debug("Deduping new records")
        new_record_counter = Counter([i.control_number for i in new])
        dupe_recs = [i for i, count in new_record_counter.items() if count > 1]
        if not dupe_recs:
            logger.debug("No duplicates found in file.")
            return {"DUP": merge, "NEW": new, "DEDUPED": deduped}
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
        return {"DUP": merge, "NEW": new, "DEDUPED": deduped}
