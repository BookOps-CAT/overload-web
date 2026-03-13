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
    library: list[str]
    collection: list[str | None]
    record_type: list[str]
    file_names: list[list[str]]
    total_files_processed: list[int]
    total_records_processed: list[int]
    missing_barcodes: list[list[str]]
    processing_integrity: list[str | None]
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
    summary: SummaryReport
    detailed_data: dict[str, list[Any]]
