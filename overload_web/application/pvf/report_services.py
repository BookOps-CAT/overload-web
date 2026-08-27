"""Application services to use when reporting on process vendor file services."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import reporting

logger = logging.getLogger(__name__)


class PVFReporter:
    @staticmethod
    def create_output_report(data: dict[str, Any], record_type: str) -> dict[str, Any]:
        """Create processing report based on data from a saved `ProcessedFileBatch`"""
        stats = reporting.ProcessingStatistics(data["processing_statistics"])
        out = {
            "total_records": data["total_records"],
            "file_names": data["file_names"],
            "total_files": len(data["file_names"]),
            "vendor_report": stats.create_vendor_report(),
            "dupes_report": stats.create_duplicate_report(),
            "missing_barcodes": data.get("missing_barcodes", []),
            "processing_integrity": data.get("processing_integrity", True),
            "call_no_report": stats.create_call_number_report(record_type=record_type),
        }
        return out


class ReportWriter:
    @staticmethod
    def write_report_to_google_sheet(
        data: dict[str, Any], writer: ports.ReportWriter, record_type: str
    ) -> None:
        """Write processing data to a google sheet."""
        stats = reporting.ProcessingStatistics(data["processing_statistics"])
        call_no_report = stats.create_call_number_report(record_type=record_type)
        if call_no_report:
            prepped_data = writer.prep_report(data=call_no_report)
            writer.write_report(prepped_data)
        prepped_data = writer.prep_report(data=stats.create_duplicate_report())
        writer.write_report(prepped_data)
