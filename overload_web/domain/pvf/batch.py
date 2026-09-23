"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import logging
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
