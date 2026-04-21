"""Application services for interacting with DomainBib objects during processing."""

from __future__ import annotations

import io
import itertools
import logging
from collections import Counter, defaultdict
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
        records: list[bibs.DomainBib], barcodes: list[str]
    ) -> list[str]:
        """Confirm barcodes extracted from a file are present in processed records"""
        valid = True
        processed_barcodes = list(
            itertools.chain.from_iterable([i.barcodes for i in records])
        )
        missing_barcodes = set()
        for barcode in barcodes:
            if barcode not in processed_barcodes:
                valid = False
                missing_barcodes.add(barcode)
        valid = sorted(barcodes) == sorted(processed_barcodes)
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
        return list(missing_barcodes)

    @staticmethod
    def ensure_unique(bibs: list[bibs.DomainBib]) -> None:
        """Confirm barcodes in a file are all unique."""
        barcodes = list(itertools.chain.from_iterable([i.barcodes for i in bibs]))
        barcode_counter = Counter(barcodes)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise OverloadError(f"Duplicate barcodes found in file: {dupe_barcodes}")


class BibDeduplicator:
    @staticmethod
    def deduplicate(
        records: list[bibs.DomainBib], engine: ports.MarcEnginePort
    ) -> dict[str, list[bibs.DomainBib]]:
        """Review and deduplicate a batch of processed full-level MARC records."""
        merge: list[bibs.DomainBib] = []
        new: list[bibs.DomainBib] = []
        deduped: list[bibs.DomainBib] = []
        for record in records:
            if record.analysis and record.analysis.action == bibs.CatalogAction.ATTACH:
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
        data: bytes, engine: ports.MarcEnginePort, vendor: str | None = "UNKNOWN"
    ) -> list[bibs.DomainBib]:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
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


class BibSerializer:
    @staticmethod
    def write(records: list[bibs.DomainBib]) -> bytes:
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
        out = io_data.getvalue()
        return out


class BibUpdatePolicy:
    @staticmethod
    def apply_full_record_updates(
        record: bibs.DomainBib, engine: ports.MarcEnginePort
    ) -> None:
        """Update and add MARC fields to processed full-level bib record"""
        bib = engine.create_bib_from_domain(record=record)
        updates = rules.CatalogingUpdates.field_list(
            record=record, context=engine.config
        )
        engine.update_fields(field_updates=updates, bib=bib)
        bib.leader = rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()

    @staticmethod
    def apply_order_record_updates(
        record: bibs.DomainBib,
        engine: ports.MarcEnginePort,
        template_data: dict[str, Any],
    ) -> None:
        """Update and add MARC fields to processed order-level bib record"""
        record.apply_order_template(template_data)
        bib = engine.create_bib_from_domain(record=record)

        if engine.record_type == "acq":
            updates = rules.AcquisitionUpdates.field_list(
                record=record, context=engine.config
            )
        else:
            updates = rules.SelectionUpdates.field_list(
                record=record,
                context=engine.config,
                format=template_data.get("format"),
                command_tag=engine.get_command_tag_field(bib),
            )
        engine.update_fields(field_updates=updates, bib=bib)
        bib.leader = rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()


class MarcFileMerger:
    @staticmethod
    def combine_marc_files(data: list[bytes], engine: ports.MarcEnginePort) -> bytes:
        """Combine multiple bytes objects (ie. MARC files) into one for processing."""
        records = []
        for batch in data:
            reader = engine.get_reader(batch)
            for record in reader:
                records.append(record)
        io_data = io.BytesIO()
        for record in records:
            io_data.write(record.as_marc())
        io_data.seek(0)
        return io_data.getvalue()


class PVFReporter:
    """Generate statistics from a batch of processed records to use in reporting."""

    @staticmethod
    def create_full_records_report(
        records: list[bibs.DomainBib],
        missing_barcodes: list[str],
        file_names: list[str],
    ) -> dict[str, list[Any]]:
        stats = defaultdict(list)
        all_recs = []
        stats["file_names"].extend(file_names)
        stats["missing_barcodes"].extend(missing_barcodes)
        all_recs.extend(records)
        for rec in all_recs:
            for k, v in rec.analysis.__dict__.items():
                stats[k].append(v)
            stats["vendor"].append(getattr(rec, "vendor", "UNKNOWN"))
        out: dict[str, Any] = dict(stats)
        out["total_records"] = len(all_recs)
        out["total_files"] = len(stats["file_names"])
        return out

    @staticmethod
    def create_order_records_report(
        records: list[bibs.DomainBib], file_names: list[str]
    ) -> dict[str, list[Any]]:
        stats = defaultdict(list)
        for rec in records:
            for k, v in rec.analysis.__dict__.items():
                stats[k].append(v)
            stats["vendor"].append(rec.vendor)
        out: dict[str, Any] = dict(stats)
        out["total_records"] = len(records)
        out["total_files"] = len(file_names)
        out["file_names"] = file_names
        return out
