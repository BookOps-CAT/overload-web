from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from overload_web.domain.models import bibs


class FileReport:
    def __init__(
        self, analyses: list[bibs.MatchAnalysis], file_name: str | None = None
    ) -> None:
        self._analyses = analyses
        self.file_name = file_name
        self.action = tuple([i.action for i in self._analyses])
        self.call_number = tuple([i.call_number for i in self._analyses])
        self.call_number_match = tuple([i.call_number_match for i in self._analyses])
        self.duplicate_records = tuple(
            [",".join(i.duplicate_records) for i in self._analyses]
        )
        self.mixed = tuple([",".join(i.mixed) for i in self._analyses])
        self.other = tuple([",".join(i.other) for i in self._analyses])
        self.resource_id = tuple([i.resource_id for i in self._analyses])
        self.target_bib_id = tuple([i.target_bib_id for i in self._analyses])
        self.target_call_no = tuple([i.target_call_no for i in self._analyses])
        self.target_title = tuple([i.target_title for i in self._analyses])
        self.updated_by_vendor = tuple([i.updated_by_vendor for i in self._analyses])
        self.vendor = tuple([i.vendor for i in self._analyses])
        self.date = datetime.date.today().strftime("%y-%m-%d")
        self.total_records = len(self._analyses)

    def to_dict(self) -> dict[str, Any]:
        record_count = len(self.action)
        return {
            "resource_id": list(self.resource_id),
            "vendor": list(self.vendor),
            "updated_by_vendor": list(self.updated_by_vendor),
            "call_number_match": list(self.call_number_match),
            "target_call_no": list(self.target_call_no),
            "call_number": list(self.call_number),
            "duplicate_records": list(self.duplicate_records),
            "target_bib_id": list(self.target_bib_id),
            "target_title": list(self.target_title),
            "mixed": list(self.mixed),
            "other": list(self.other),
            "action": list(self.action),
            "corrected": ["no"] * record_count,
            "file_name": self.file_name,
        }


@dataclass
class SummaryReport:
    library: str
    collection: str
    record_type: str
    file_names: list[str]
    total_files_processed: int
    total_records_processed: int
    vendor_breakdown: dict[str, Any]
    duplicates_report: Any | None = None
    call_number_issues: Any | None = None
