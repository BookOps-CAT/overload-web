"""Domain models that define reports and their component parts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatistics:
    action: list[str | None]
    call_number: list[str | None]
    call_number_match: list[bool | None]
    duplicate_records: list[list[str | None]]
    file_names: list[str | None]
    mixed: list[list[str | None]]
    other: list[list[str | None]]
    resource_id: list[str | None]
    target_bib_id: list[str | None]
    target_call_no: list[str | None]
    target_title: list[str | None]
    total_files: int
    total_records: int
    updated_by_vendor: list[bool]
    vendor: list[str | None]
    missing_barcodes: list[str | None] = field(default_factory=list)
    processing_integrity: bool = True

    @property
    def call_number_report_data(self) -> dict[str, list[Any]]:
        return {
            "vendor": self.vendor,
            "resource_id": self.resource_id,
            "call_number": self.call_number,
            "target_bib_id": self.target_bib_id,
            "target_call_no": self.target_call_no,
            "call_number_match": self.call_number_match,
            "duplicate_records": self.duplicate_records,
        }

    @property
    def detailed_report_data(self) -> dict[str, list[Any]]:
        return {
            "vendor": self.vendor,
            "resource_id": self.resource_id,
            "action": self.action,
            "target_bib_id": self.target_bib_id,
            "updated_by_vendor": self.updated_by_vendor,
            "call_number_match": self.call_number_match,
            "call_number": self.call_number,
            "target_call_no": self.target_call_no,
            "duplicate_records": self.duplicate_records,
            "mixed": self.mixed,
            "other": self.other,
        }

    @property
    def duplicate_report_data(self) -> dict[str, list[Any]]:
        return {
            "vendor": self.vendor,
            "resource_id": self.resource_id,
            "target_bib_id": self.target_bib_id,
            "duplicate_records": self.duplicate_records,
            "mixed": self.mixed,
            "other": self.other,
        }

    @property
    def vendor_report_data(self) -> dict[str, list[Any]]:
        return {"action": self.action, "vendor": self.vendor}
