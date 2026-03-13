"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFullMarcFile:
    """A dataclass representing a processed file of records."""

    merge_records: list[bibs.DomainBib]
    insert_records: list[bibs.DomainBib]
    deduplicated_records: list[bibs.DomainBib]
    missing_barcodes: list[str]


@dataclass
class ProcessedOrderMarcFile:
    """A dataclass representing a processed file of records."""

    file_name: str
    records: list[bibs.DomainBib]
