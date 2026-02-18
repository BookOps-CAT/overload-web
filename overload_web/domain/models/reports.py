from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, BinaryIO, TypedDict

from overload_web.domain.models import bibs

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


@dataclass
class ProcessedFullRecordsBatch:
    """A dataclass representing a processed file of records."""

    duplicate_records: list[bibs.DomainBib]
    new_records: list[bibs.DomainBib]
    deduplicated_records: list[bibs.DomainBib]
    duplicate_records_stream: BinaryIO
    new_records_stream: BinaryIO
    deduplicated_records_stream: BinaryIO
    missing_barcodes: list[str]
    file_name: str
    library: str
    collection: str | None
    record_type: str


@dataclass
class ProcessedOrderRecordsBatch:
    """A dataclass representing a processed file of records."""

    records: list[bibs.DomainBib]
    record_stream: BinaryIO
    file_name: str
    library: str
    collection: str | None
    record_type: str


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
class AllReportData:
    summary: SummaryReport
    detailed_data: dict[str, list[Any]]
