"""Application serivce commands for reporting operations."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.pvf import report_services

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
            return report_services.PVFReporter.create_output_report(
                data=data, record_type=record_type
            )
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
            report_services.ReportWriter.write_report_to_google_sheet(
                data=data, writer=writer, record_type=record_type
            )
