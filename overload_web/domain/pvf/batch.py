"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import itertools
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFile:
    """A value object representing a processed file of MARC records"""

    file_name: str
    records: bytes


class ProcessedFileBatch:
    """A dataclass representing a batch of processed files and their statistics"""

    def __init__(
        self,
        stats: list[dict[str, Any]],
        file_names: list[str],
        files: list[ProcessedFile],
        missing_barcodes: list[str] | None = None,
    ) -> None:
        self.files = files
        self.stats = stats
        self.file_names = file_names
        self.total_files = len(file_names)
        self.total_records = len(stats)
        self.missing_barcodes = missing_barcodes
        self.processing_integrity = missing_barcodes in [[], None]


class BarcodeValidator:
    @classmethod
    def validate_unique(cls, barcodes: list[list[str]]) -> list[str]:
        """Confirm barcodes in a file are all unique."""
        barcode_list = list(itertools.chain.from_iterable(barcodes))
        barcode_counter = Counter(barcode_list)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise ValueError(f"Duplicate barcodes found in file: {dupe_barcodes}")
        return barcode_list

    @classmethod
    def validate_preserved(
        cls, processed_barcodes: list[list[str]], original_barcodes: list[str]
    ) -> list[str]:
        """Confirm barcodes extracted from a file are present in processed records"""
        missing_barcodes = set()
        processed = list(itertools.chain.from_iterable(processed_barcodes))
        for barcode in original_barcodes:
            if barcode not in processed:
                missing_barcodes.add(barcode)
        missing_barcodes = set(original_barcodes) - set(processed)
        valid = len(missing_barcodes) == 0
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
        return list(missing_barcodes)
