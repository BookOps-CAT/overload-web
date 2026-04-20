import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.models import reporting

logger = logging.getLogger(__name__)


class PVFReporter:
    @staticmethod
    def create_output_report(
        data: dict[str, Any], handler: ports.ReportHandler, record_type: str
    ) -> dict[str, Any]:
        stats = reporting.ProcessingStatistics(**data)
        out = {
            "total_records": data["total_records"],
            "file_names": data["file_names"],
            "total_files": len(data["file_names"]),
        }
        vendor = handler.create_vendor_report(report_data=stats.vendor_report_data)
        call_no = handler.create_call_number_report(
            report_data=stats.call_number_report_data, record_type=record_type
        )
        dupes = handler.create_duplicate_report(report_data=stats.duplicate_report_data)
        if record_type == "cat":
            out.update(
                {
                    "missing_barcodes": data["missing_barcodes"],
                    "processing_integrity": data["processing_integrity"],
                }
            )
        out.update(
            {
                "vendor_report": vendor,
                "dupes_report": dupes,
                "call_no_report": call_no,
                "duplicate_bibs": None,
            }
        )
        return out

    @staticmethod
    def create_detailed_report(
        data: dict[str, Any], handler: ports.ReportHandler
    ) -> dict[str, Any]:
        stats = reporting.ProcessingStatistics(**data)
        return handler.create_detailed_report(report_data=stats.detailed_report_data)


class ReportWriter:
    @staticmethod
    def write_report_to_google_sheet(
        data: dict[str, Any],
        handler: ports.ReportHandler,
        writer: ports.ReportWriter,
        record_type: str,
    ) -> None:
        stats = reporting.ProcessingStatistics(**data)
        call_no = handler.create_call_number_report(
            report_data=stats.call_number_report_data, record_type=record_type
        )
        dupes = handler.create_duplicate_report(report_data=stats.duplicate_report_data)
        if call_no:
            prepped_data = writer.prep_report(data=call_no)
            writer.write_report(prepped_data)
        duplicates_report = handler.create_duplicate_report(dupes)
        prepped_data = writer.prep_report(data=duplicates_report)
        writer.write_report(prepped_data)
