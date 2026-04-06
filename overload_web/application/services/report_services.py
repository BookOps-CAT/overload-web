import logging
from collections import defaultdict
from typing import Any

from overload_web.application import ports
from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class PVFReporter:
    @staticmethod
    def create_full_records_report(
        records: list[bibs.DomainBib],
        missing_barcodes: list[str],
        file_names: list[str],
    ) -> bibs.ProcessingStatistics:
        stats = defaultdict(list)
        all_recs = []
        stats["file_names"].extend(file_names)
        stats["missing_barcodes"].extend(missing_barcodes)
        all_recs.extend(records)
        for rec in all_recs:
            for k, v in rec.analysis.__dict__.items():
                stats[k].append(v)
            stats["vendor"].append(getattr(rec, "vendor", "UNKNOWN"))
        out: dict[str, Any] = dict(stats)
        out["total_records"] = len(all_recs)
        out["total_files"] = len(stats["file_names"])
        return bibs.ProcessingStatistics(**out)

    @staticmethod
    def create_order_records_report(
        records: list[bibs.DomainBib], file_names: list[str]
    ) -> bibs.ProcessingStatistics:
        stats = defaultdict(list)
        for rec in records:
            for k, v in rec.analysis.__dict__.items():
                stats[k].append(v)
            stats["vendor"].append(rec.vendor)
        out: dict[str, Any] = dict(stats)
        out["total_records"] = len(records)
        out["total_files"] = len(file_names)
        out["file_names"] = file_names
        return bibs.ProcessingStatistics(**out)

    @staticmethod
    def create_output_report(
        data: dict[str, Any], handler: ports.ReportHandler, record_type: str
    ) -> dict[str, Any]:
        stats = bibs.ProcessingStatistics(**data)
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
        stats = bibs.ProcessingStatistics(**data)
        return handler.create_detailed_report(report_data=stats.detailed_report_data)


class ReportWriter:
    @staticmethod
    def write_report_to_google_sheet(
        data: bibs.ProcessingStatistics,
        handler: ports.ReportHandler,
        writer: ports.ReportWriter,
        record_type: str,
    ) -> None:
        call_no_report = handler.create_call_number_report(
            data.call_number_report_data, record_type=record_type
        )
        if call_no_report:
            prepped_data = writer.prep_report(data=call_no_report)
            writer.write_report(prepped_data)
        duplicates_report = handler.create_duplicate_report(data.duplicate_report_data)
        prepped_data = writer.prep_report(data=duplicates_report)
        writer.write_report(prepped_data)
