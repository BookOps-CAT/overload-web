from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class CallNumberReport(TypedDict):
    vendor: list[str]
    resource_id: list[str]
    target_bib_id: list[str]
    duplicate_records: list[str]
    call_number_match: list[str]
    call_number: list[str]
    target_call_no: list[str]


class DuplicateReport(TypedDict):
    vendor: list[str]
    resource_id: list[str]
    target_bib_id: list[str]
    duplicate_records: list[str]
    mixed: list[str]
    other: list[str]


class VendorReport(TypedDict):
    vendor: list[str]
    attach: list[str]
    insert: list[str]
    update: list[str]
    total: list[str]


@dataclass
class ProcessingStatistics:
    action: list[str]
    call_number: list[str]
    call_number_match: list[str]
    duplicate_records: list[str]
    file_names: list[str]
    mixed: list[str]
    other: list[str]
    resource_id: list[str]
    target_bib_id: list[str]
    target_call_no: list[str]
    target_title: list[str]
    total_files: int
    total_records: int
    updated_by_vendor: list[str]
    vendor: list[str]
    missing_barcodes: list[str] = field(default_factory=list)
    processing_integrity: bool = True

    @property
    def call_number_report_data(self) -> dict[str, list[Any]]:
        return {
            "resource_id": self.resource_id,
            "target_bib_id": self.target_bib_id,
            "call_number_match": self.call_number_match,
            "call_number": self.call_number,
            "target_call_no": self.target_call_no,
            "duplicate_records": self.duplicate_records,
            "vendor": self.vendor,
        }

    @property
    def duplicate_report_data(self) -> dict[str, list[Any]]:
        return {
            "resource_id": self.resource_id,
            "target_bib_id": self.target_bib_id,
            "mixed": self.mixed,
            "other": self.other,
            "duplicate_records": self.duplicate_records,
            "vendor": self.vendor,
        }

    @property
    def vendor_report_data(self) -> dict[str, list[Any]]:
        return {"action": self.action, "vendor": self.vendor}
