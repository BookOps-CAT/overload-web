"""Application serivce commands for reporting operations."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import reporting

logger = logging.getLogger(__name__)


class CreatePVFOutputReport:
    @staticmethod
    def execute(
        batch_id: str, record_type: str, repo: ports.SqlRepositoryProtocol
    ) -> dict[str, Any]:
        """
        Create a report summary for a batch of processed records.

        Args:
            batch_id:
                The ID for the `ProcessedFileBatch` object in the database.
            record_type:
                The record type for the operation as a string.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
        Returns:
            The report data as a dictionary.
        """
        data = repo.get(batch_id)
        if data:
            stats = reporting.ProcessingStatistics(data["processing_statistics"])
            return {
                "total_records": data["total_records"],
                "file_names": data["file_names"],
                "total_files": len(data["file_names"]),
                "vendor_report": stats.create_vendor_report(),
                "dupes_report": stats.create_duplicate_report(),
                "missing_barcodes": data.get("missing_barcodes", []),
                "processing_integrity": data.get("processing_integrity", True),
                "call_no_report": stats.create_call_number_report(
                    record_type=record_type
                ),
            }
        return {}


class GetDetailedReportData:
    @staticmethod
    def execute(
        batch_id: str, repo: ports.SqlRepositoryProtocol
    ) -> list[dict[str, Any]]:
        """
        Create a detailed processing report for a batch of processed records.

        Args:
            batch_id:
                The ID for the `ProcessedFileBatch` object in the database.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
        Returns:
            The report data as a dictionary.
        """
        data = repo.get(batch_id)
        if data:
            return data["processing_statistics"]
        return []


class WriteOutputReport:
    @staticmethod
    def execute(
        batch_id: str,
        record_type: str,
        repo: ports.SqlRepositoryProtocol,
        writer: ports.ReportWriter,
    ) -> None:
        """
        Write processing statistics to a google sheet.

        Args:
            batch_id:
                The ID for the `ProcessedFileBatch` object in the database.
            record_type:
                The record type for the operation as a string.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
            writer:
                a `ports.ReportWriter` object used by the command.
        Returns:
            The report data as a dictionary.
        """
        data = repo.get(batch_id)
        if data:
            stats = reporting.ProcessingStatistics(data["processing_statistics"])
            call_no_report = stats.create_call_number_report(record_type=record_type)
            if call_no_report:
                prepped_data = writer.prep_report(data=call_no_report)
                writer.write_report(prepped_data)
            prepped_data = writer.prep_report(data=stats.create_duplicate_report())
            writer.write_report(prepped_data)
