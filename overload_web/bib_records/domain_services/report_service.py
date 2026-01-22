"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)

C = TypeVar("C")
D = TypeVar("D", covariant=True)


class ReportHandler(Protocol[C]):
    def configure_sheet(self) -> C: ...  # pragma: no branch

    def write_data_to_sheet(
        self, data: dict, spreadsheet_id: str, creds: C, sheet_name: str
    ) -> dict | None: ...  # pragma: no branch


class FileReporter(Protocol[D]):
    handler: ReportHandler

    def report_on_analysis(
        self, report_data: list[bibs.MatchAnalysis]
    ) -> dict[str, Any]: ...  # pragma: no branch

    def create_duplicate_report(
        self, data: dict[str, Any]
    ) -> D: ...  # pragma: no branch

    def create_call_number_report(
        self, data: dict[str, Any]
    ) -> D: ...  # pragma: no branch

    def export_duplicate_report_for_sheet(
        self, data: dict[str, Any]
    ) -> list[list[Any]]: ...  # pragma: no branch

    def export_call_number_report_for_sheet(
        self, data: dict[str, Any]
    ) -> list[list[Any]]: ...  # pragma: no branch
