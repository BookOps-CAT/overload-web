from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TypedDict

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
    total_files_processed: int
    total_records_processed: int
    updated_by_vendor: list[str]
    vendor: list[str]
    missing_barcodes: list[str] = field(default_factory=list)
    processing_integrity: bool = True
