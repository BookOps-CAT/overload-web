from dataclasses import dataclass

from overload_web.domain.models import bibs, reports


@dataclass
class ProcessedFileBatch:
    """A dataclass representing a batch of processed files and their statistics"""

    files: list[bibs.ProcessedFile]
    report: reports.ProcessingStatistics
