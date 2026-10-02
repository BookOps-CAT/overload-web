"""Domain services for parsing, reviewing and updating MARC records during processing"""

from __future__ import annotations

import io
import itertools
import logging
from collections import Counter, defaultdict
from typing import Any

from overload_web.domain.pvf import marc_rules, models, ports

logger = logging.getLogger(__name__)


class BarcodeValidator:
    def validate_unique(self, barcodes: list[list[str]]) -> list[str]:
        """Confirm barcodes in a file are all unique."""
        barcode_list = list(itertools.chain.from_iterable(barcodes))
        barcode_counter = Counter(barcode_list)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise ValueError(f"Duplicate barcodes found in file: {dupe_barcodes}")
        return barcode_list

    def validate_preserved(
        self, processed_barcodes: list[list[str]], original_barcodes: list[str]
    ) -> list[str]:
        """Confirm all barcodes extracted from file are present in processed records"""
        missing_barcodes = set()
        processed = list(itertools.chain.from_iterable(processed_barcodes))
        for barcode in original_barcodes:
            if barcode not in processed:
                missing_barcodes.add(barcode)
        missing_barcodes = set(original_barcodes) - set(processed)
        valid = len(missing_barcodes) == 0
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
        return list(missing_barcodes)


class BibParser:
    def __init__(
        self,
        bib_mapping: dict[str, Any],
        collection: str | None,
        handler: ports.MarcParserPort,
        library: str,
        order_mapping: dict[str, Any],
        record_type: str,
        vendor_mapping: dict[str, Any],
    ) -> None:
        """
        Initialize `BibParser` using a set of mapping rules and inputs.

        Args:
            bib_mapping:
                rules for mapping bookops_marc.Bib objects to domain objects
            collection:
                the collection to which the records belong
            handler:
                a `MarcParserPort` object used to handle interactions with pymarc
            library:
                the library whose records are being parsed
            order_mapping:
                rules for mapping bookops_marc.Order objects to domain objects
            record_type:
                the workflow two whom this record belongs
            vendor_mapping:
                rules for identifying the vendor to whom a record belongs
        """
        self.bib_mapping = bib_mapping
        self.collection = collection
        self.handler = handler
        self.library = library
        self.order_mapping = order_mapping
        self.record_type = record_type
        self.vendor_mapping = vendor_mapping

    def combine_marc_files(self, data: list[bytes]) -> bytes:
        """Combine multiple bytes objects (ie. MARC files) into one for processing."""
        records = []
        for batch in data:
            reader = self.handler.get_reader(batch, library=self.library)
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
        binary_data: bytes,
        collection: str | None,
        order_data: list[dict[str, Any]],
        vendor: str | None,
        vendor_info: dict[str, Any] | None,
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
        self, data: bytes, vendor: str | None = "UNKNOWN"
    ) -> list[models.DomainBib]:
        """Parse MARC binary to a list of `DomainBib` domain objects."""
        vendor_info: dict[str, Any] | None
        parsed = []
        reader = self.handler.get_reader(data, library=self.library)
        for record in reader:
            bib_dict = self.handler.map_bib_data(obj=record, mapping=self.bib_mapping)
            order_data = [
                self.handler.map_order_data(obj=i, mapping=self.order_mapping)
                for i in record.orders
            ]
            if self.record_type == "cat":
                vendor_info = self.handler.identify_vendor(
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

    def write(self, records: list[models.DomainBib]) -> bytes:
        return self.handler.write(records=[i.binary_data for i in records])


class BibReviewer:
    def __init__(self, handler: ports.MarcUpdaterPort) -> None:
        self.handler = handler

    def review_batch(self, records: list[models.DomainBib]) -> dict[str, Any]:
        """Merges item fields from duplicate records into a base record."""
        out: dict[str, list[models.DomainBib]] = {"NEW": [], "DUP": [], "DEDUPED": []}
        dup_groups = defaultdict(list)

        for record in records:
            if record.action and record.action == "attach":
                out["DUP"].append(record)
            else:
                out["NEW"].append(record)
                dup_groups[record.control_number].append(record)
        for control_number, group in dup_groups.items():
            # only deduplicate new recs if there are groups with multiple records
            if len(group) > 1 and control_number is not None:
                return {"NEW": out["NEW"], "DUP": out["DUP"], "TO_DEDUPE": dup_groups}
        return {"NEW": out["NEW"], "DUP": out["DUP"]}

    def deduplicate(self, batches: dict[str, Any]) -> dict[str, list[models.DomainBib]]:
        """Review and deduplicate a batch of processed full-level MARC records."""
        if not batches.get("TO_DEDUPE"):
            return {"NEW": batches["NEW"], "DUP": batches["DUP"], "DEDUPED": []}
        deduped = []
        for control_number, group in batches["TO_DEDUPE"].items():
            if len(group) == 1:
                deduped.append(group[0])
            elif len(group) > 1 and control_number is not None:
                base_rec = group[0]
                other_fields = [i.parsed_fields for i in group[1:]]
                item_tags = marc_rules.FieldRules.get_item_field_criteria(
                    fields=base_rec.parsed_fields, library=base_rec.library
                )
                item_fields = marc_rules.FieldRules.get_item_fields(
                    fields=other_fields, criteria=item_tags
                )
                bib = self.handler.create_bib_from_domain(
                    binary_data=base_rec.binary_data, library=base_rec.library
                )
                self.handler.update_fields(field_updates=item_fields, bib=bib)
                base_rec.binary_data = bib.as_marc()
                deduped.append(base_rec)
            else:
                deduped.extend(group)
        return {"NEW": batches["NEW"], "DUP": batches["DUP"], "DEDUPED": deduped}


class BibUpdater:
    def __init__(
        self,
        bib_id_tag: str,
        default_loc: str | None,
        handler: ports.MarcUpdaterPort,
        library: str,
        order_mapping: dict[str, Any],
        record_type: str,
    ) -> None:
        """
        Initialize `BibUpdater` using a set of rules and inputs.

        Args:
            bib_id_tag:
                MARC tag where bib ID should be writting in output record.
            default_loc:
                The default location for a specific library/collection to be used
                in output record
            handler:
                a `MarcUpdaterPort` object used to handle interactions with pymarc
            library:
                the library whose records are being parsed
            order_mapping:
                rules for mapping domain objects MARC fields/subfields
            record_type:
                the workflow two whom this record belongs
        """
        self.bib_id_tag = bib_id_tag
        self.default_loc = default_loc
        self.handler = handler
        self.library = library
        self.order_mapping = order_mapping
        self.record_type = record_type

    def apply_field_updates(
        self, record: models.DomainBib, updates: list[marc_rules.MarcFieldUpdateValues]
    ) -> None:
        """Update and add MARC fields to bib record"""
        bib = self.handler.create_bib_from_domain(
            binary_data=record.binary_data, library=record.library
        )
        self.handler.update_fields(field_updates=updates, bib=bib)
        self.handler.update_leader_encoding(leader=bib.leader, bib=bib)
        record.binary_data = bib.as_marc()

    def get_full_record_updates(
        self, record: models.DomainBib
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to add to or update in processed bib record"""
        updates: list[Any] = []

        updates.extend(
            marc_rules.FieldRules.add_vendor_fields(
                getattr(record.vendor_info, "bib_fields", [])
            )
        )
        updates.append(
            marc_rules.FieldRules.add_bib_id(bib_id=record.bib_id, tag=self.bib_id_tag)
        )
        if self.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record.collection))
            updates.append(
                marc_rules.FieldRules.update_bt_series_call_no(
                    call_no=record.branch_call_number,
                    vendor=record.vendor,
                    collection=record.collection,
                )
            )
        return [i for i in updates if i]

    def get_order_level_updates(
        self, record: models.DomainBib, template_data: dict[str, Any]
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to add to or update in processed bib record"""
        updates: list[Any] = []
        record.apply_order_template(template_data)
        updates.extend(
            marc_rules.FieldRules.update_order_fields(
                orders=record.orders, mapping=self.order_mapping
            )
        )
        if self.record_type == "sel":
            updates.append(
                marc_rules.FieldRules.add_command_tag(
                    fields=record.parsed_fields,
                    format=template_data.get("format"),
                    default_loc=self.default_loc,
                )
            )
            updates.append(
                marc_rules.FieldRules.add_bib_id(
                    bib_id=record.bib_id, tag=self.bib_id_tag
                )
            )
        if self.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record.collection))
        return [i for i in updates if i]
