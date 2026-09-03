"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import itertools
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any

from overload_web.domain.pvf import models

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
    @staticmethod
    def validate_unique(records: list[models.DomainBib]) -> list[str]:
        """Confirm barcodes in a file are all unique."""
        barcodes = list(itertools.chain.from_iterable([i.barcodes for i in records]))
        barcode_counter = Counter(barcodes)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise ValueError(f"Duplicate barcodes found in file: {dupe_barcodes}")
        return barcodes

    @classmethod
    def validate_preserved(
        cls, processed_records: list[models.DomainBib], original_barcodes: list[str]
    ) -> list[str]:
        """Confirm barcodes extracted from a file are present in processed records"""
        missing_barcodes = set()
        processed_barcodes = list(
            itertools.chain.from_iterable([i.barcodes for i in processed_records])
        )
        for barcode in original_barcodes:
            if barcode not in processed_barcodes:
                missing_barcodes.add(barcode)
        missing_barcodes = set(original_barcodes) - set(processed_barcodes)
        valid = len(missing_barcodes) == 0
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")
        return list(missing_barcodes)
