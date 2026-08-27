"""Domain models that define reports and their component parts."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFile:
    """A value object representing a processed file of MARC records"""

    file_name: str
    records: bytes


@dataclass
class ProcessedFileBatch:
    """A dataclass representing a batch of processed files and their statistics"""

    files: list[ProcessedFile]
    report: ProcessingStatistics


@dataclass
class ProcessingStatistics:
    """A value object representing a statistics for a batch of processed files"""

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
            "action": self.action,
            "call_number": self.call_number,
            "call_number_match": self.call_number_match,
            "duplicate_records": self.duplicate_records,
            "mixed": self.mixed,
            "other": self.other,
            "resource_id": self.resource_id,
            "target_bib_id": self.target_bib_id,
            "target_call_no": self.target_call_no,
            "updated_by_vendor": self.updated_by_vendor,
            "vendor": self.vendor,
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

    @classmethod
    def create_full_records_report(
        cls,
        analysis: list[dict[str, Any]],
        missing_barcodes: list[str],
        file_names: list[str],
    ) -> ProcessingStatistics:
        """Generate statistics from a batch of processed full-level records"""
        stats = defaultdict(list)
        for rec in analysis:
            for k, v in rec.items():
                stats[k].append(v)
        out: dict[str, Any] = dict(stats)
        out["total_records"] = len(analysis)
        out["total_files"] = len(stats["file_names"])
        out["file_names"] = file_names
        out["missing_barcodes"] = missing_barcodes
        return cls(**out)

    @classmethod
    def create_order_records_report(
        cls, analysis: list[dict[str, Any]], file_names: list[str]
    ) -> ProcessingStatistics:
        """Generate statistics from a batch of processed order-level records"""
        stats = defaultdict(list)
        for rec in analysis:
            for k, v in rec.items():
                stats[k].append(v)
        out: dict[str, Any] = dict(stats)
        out["total_records"] = len(analysis)
        out["total_files"] = len(file_names)
        out["file_names"] = file_names
        return cls(**out)
