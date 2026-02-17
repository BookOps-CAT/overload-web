"""Domain models that define bib records, order records, and their component parts."""

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
    updated: list[str]
    call_number_match: list[str]
    call_number: list[str]
    target_call_no: list[str]
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


class VendorReport(TypedDict):
    vendor: list[str]
    attach: list[str]
    insert: list[str]
    update: list[str]
    total: list[str]


@dataclass
class AllReportData:
    summary: dict[str, list[Any]]
    vendor_breakdown: dict[str, list[Any]]
    detailed_data: dict[str, list[Any]]
    duplicates_report: dict[str, list[Any]] | None = None
    call_number_issues: dict[str, list[Any]] | None = None
