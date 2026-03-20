from __future__ import annotations

import logging
from dataclasses import dataclass
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


class DetailedReport(TypedDict):
    vendor: list[str]
    resource_id: list[str]
    action: list[str]
    target_bib_id: list[str]
    updated_by_vendor: list[str]
    call_number_match: list[str]
    call_number: list[str]
    target_call_no: list[str]
    target_title: list[str]
    duplicate_records: list[str]
    mixed: list[str]
    other: list[str]


class DuplicateReport(TypedDict):
    vendor: list[str]
    resource_id: list[str]
    target_bib_id: list[str]
    duplicate_records: list[str]
    mixed: list[str]
    other: list[str]


class SummaryReport(TypedDict):
    file_names: list[str]
    total_files_processed: int
    total_records_processed: int
    missing_barcodes: list[str]
    processing_integrity: str | None
    vendor_breakdown: VendorReport
    duplicates_report: DuplicateReport | None
    call_number_issues: CallNumberReport | None


class VendorReport(TypedDict):
    vendor: list[str]
    attach: list[str]
    insert: list[str]
    update: list[str]
    total: list[str]


@dataclass
class ProcessingStatistics:
    file_names: list[str]
    total_files_processed: int
    total_records_processed: int
    missing_barcodes: list[str]
    processing_integrity: bool
    vendor_breakdown: VendorReport
    duplicates_report: DuplicateReport | None
    call_number_issues: CallNumberReport | None
    detailed_data: dict[str, list[Any]]


@dataclass
class OrderProcessingStatistics:
    summary: SummaryReport
    detailed_data: dict[str, list[Any]]
