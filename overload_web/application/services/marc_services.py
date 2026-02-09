from __future__ import annotations

import itertools
import logging
from collections import Counter
from typing import Any, BinaryIO

from overload_web.application.ports import marc
from overload_web.domain.errors import OverloadError
from overload_web.domain.models import bibs, rules

logger = logging.getLogger(__name__)


class BibParser:
    @staticmethod
    def parse_marc_data(
        data: BinaryIO | bytes,
        engine: marc.MarcEnginePort,
        vendor: str | None = "UNKNOWN",
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
            bib = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {bib}")
            parsed.append(bib)
        return parsed


class BarcodeExtractor:
    @staticmethod
    def extract_barcodes(records: list[bibs.DomainBib]) -> list[str]:
        """Extract all barcodes from a list of `DomainBib` objects"""
        return list(itertools.chain.from_iterable([i.barcodes for i in records]))


class BarcodeValidator:
    @staticmethod
    def ensure_unique(bibs: list[bibs.DomainBib]) -> None:
        barcodes = list(itertools.chain.from_iterable([i.barcodes for i in bibs]))
        barcode_counter = Counter(barcodes)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise OverloadError(f"Duplicate barcodes found in file: {dupe_barcodes}")


class BibUpdater:
    @staticmethod
    def update_record(
        record: bibs.DomainBib, engine: marc.MarcEnginePort, **kwargs: Any
    ) -> None:

        template_data = kwargs.get("template_data", {})
        bib = engine.create_bib_from_domain(record=record)

        updates = rules.VendorRules.fields_to_update(
            record=record,
            template_data=template_data,
            call_no=engine.get_value_of_field(tag="091", bib=bib),
            command_tag=engine.get_command_tag_field(bib),
            context=engine._config,
        )
        engine.update_fields(field_updates=updates, bib=bib)
        bib.leader = rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()
