"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any

from overload_web.domain.models import reporting

logger = logging.getLogger(__name__)


def create_full_records_report(
    analysis: list[dict[str, Any]], missing_barcodes: list[str], file_names: list[str]
) -> reporting.ProcessingStatistics:
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
    return reporting.ProcessingStatistics(**out)


def create_order_records_report(
    analysis: list[dict[str, Any]], file_names: list[str]
) -> reporting.ProcessingStatistics:
    """Generate statistics from a batch of processed order-level records"""
    stats = defaultdict(list)
    for rec in analysis:
        for k, v in rec.items():
            stats[k].append(v)
    out: dict[str, Any] = dict(stats)
    out["total_records"] = len(analysis)
    out["total_files"] = len(file_names)
    out["file_names"] = file_names
    return reporting.ProcessingStatistics(**out)


def validate_preserved_barcodes(
    processed_barcodes: list[str], original_barcodes: list[str]
) -> list[str]:
    """Confirm barcodes extracted from a file are present in processed records"""
    missing_barcodes = set()
    for barcode in original_barcodes:
        if barcode not in processed_barcodes:
            missing_barcodes.add(barcode)
    valid = sorted(original_barcodes) == sorted(processed_barcodes)
    logger.debug(
        f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
    )
    if not valid:
        logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
    return list(missing_barcodes)


def validate_unique_barcodes(barcodes: list[str]) -> None:
    """Confirm barcodes in a file are all unique."""
    barcode_counter = Counter(barcodes)
    dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
    if dupe_barcodes:
        raise ValueError(f"Duplicate barcodes found in file: {dupe_barcodes}")
