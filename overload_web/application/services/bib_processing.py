"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import itertools
import logging
from collections import Counter, defaultdict
from typing import Any

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


def create_full_records_report(
    analysis: list[bibs.MatchAnalysis],
    missing_barcodes: list[str],
    file_names: list[str],
) -> dict[str, list[Any]]:
    """Generate statistics from a batch of processed full-level records"""
    stats = defaultdict(list)
    stats["file_names"].extend(file_names)
    stats["missing_barcodes"].extend(missing_barcodes)
    for rec in analysis:
        for k, v in rec.__dict__.items():
            stats[k].append(v)
    out: dict[str, Any] = dict(stats)
    out["total_records"] = len(analysis)
    out["total_files"] = len(stats["file_names"])
    return out


def create_order_records_report(
    analysis: list[bibs.MatchAnalysis], file_names: list[str]
) -> dict[str, list[Any]]:
    """Generate statistics from a batch of processed order-level records"""
    stats = defaultdict(list)
    for rec in analysis:
        for k, v in rec.__dict__.items():
            stats[k].append(v)
    out: dict[str, Any] = dict(stats)
    out["total_records"] = len(analysis)
    out["total_files"] = len(file_names)
    out["file_names"] = file_names
    return out


def extract_barcodes(records: list[bibs.DomainBib]) -> list[str]:
    """Extract all barcodes from a list of `DomainBib` objects"""
    return list(itertools.chain.from_iterable([i.barcodes for i in records]))


def validate_preserved_barcodes(
    records: list[bibs.DomainBib], barcodes: list[str]
) -> list[str]:
    """Confirm barcodes extracted from a file are present in processed records"""
    valid = True
    processed_barcodes = list(
        itertools.chain.from_iterable([i.barcodes for i in records])
    )
    missing_barcodes = set()
    for barcode in barcodes:
        if barcode not in processed_barcodes:
            valid = False
            missing_barcodes.add(barcode)
    valid = sorted(barcodes) == sorted(processed_barcodes)
    logger.debug(
        f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
    )
    if not valid:
        logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
    return list(missing_barcodes)


def validate_unique_barcodes(bibs: list[bibs.DomainBib]) -> None:
    """Confirm barcodes in a file are all unique."""
    barcodes = list(itertools.chain.from_iterable([i.barcodes for i in bibs]))
    barcode_counter = Counter(barcodes)
    dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
    if dupe_barcodes:
        raise ValueError(f"Duplicate barcodes found in file: {dupe_barcodes}")
