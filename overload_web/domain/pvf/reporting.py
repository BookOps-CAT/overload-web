"""Domain models that define reports and their component parts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatistics:
    """A value object representing a statistics for a batch of processed files"""

    processing_statistics: list[dict[str, Any]]

    def create_call_number_report(
        self, record_type: str
    ) -> list[dict[str, Any]] | None:
        out_report = []
        for row in self.processing_statistics:
            row_report = {
                "vendor": row["vendor"],
                "resource_id": row["resource_id"],
                "target_bib_id": row["target_bib_id"],
                "duplicate_records": row["duplicate_records"],
                "call_number": row["call_number"],
                "target_call_no": row["target_call_no"],
                "call_number_match": row["call_number_match"],
            }
            if not row["call_number_match"]:
                out_report.append(row_report)
            elif (
                record_type == "cat"
                and row["call_number"] is None
                and row["target_call_no"] is None
            ):
                out_report.append(row_report)
        if out_report:
            return out_report
        return None

    def create_duplicate_report(self) -> list[dict[str, Any]]:
        out = []
        for row in self.processing_statistics:
            if row["duplicate_records"] or row["mixed"] or row["other"]:
                out.append(
                    {
                        "vendor": row["vendor"],
                        "resource_id": row["resource_id"],
                        "target_bib_id": row["target_bib_id"],
                        "duplicate_records": row["duplicate_records"],
                        "mixed": row["mixed"],
                        "other": row["other"],
                    }
                )
        return out

    def create_vendor_report(self) -> list[dict[str, Any]]:
        vendor_data: dict[str, dict[str, Any]] = {}
        for row in self.processing_statistics:
            vendor = row["vendor"]
            summary = vendor_data.setdefault(
                vendor, {"vendor": vendor, "attach": 0, "insert": 0, "update": 0}
            )
            summary[row["action"]] += 1
        for summary in vendor_data.values():
            summary["total"] = summary["attach"] + summary["insert"] + summary["update"]
        return list(vendor_data.values())
