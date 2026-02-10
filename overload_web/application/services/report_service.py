import logging
from typing import Any

import pandas as pd

from overload_web.domain.models import bibs, reports

logger = logging.getLogger(__name__)


class ReportGenerator:
    @staticmethod
    def processing_report(
        records: list[bibs.DomainBib], file_name: str | None = None
    ) -> list[bibs.MatchAnalysis]:
        report_data = []
        for record in records:
            if not record.analysis:
                raise ValueError("Bib record lacks processing report")
            report_data.append(record.analysis)
        return report_data

    @staticmethod
    def vendor_breakdown(report_data: list[bibs.MatchAnalysis]) -> dict[str, list[Any]]:
        report = reports.FileReport(report_data)
        data_dict = {
            k: v for k, v in report.to_dict().items() if k in ["vendor", "action"]
        }
        df = pd.DataFrame(data=data_dict)
        out: dict[str, list[Any]] = {
            "vendor": [],
            "attach": [],
            "insert": [],
            "update": [],
            "total": [],
        }
        for vendor, data in df.groupby("vendor"):
            attach = data[data["action"] == "attach"]["action"].count()
            insert = data[data["action"] == "insert"]["action"].count()
            update = data[data["action"] == "overlay"]["action"].count()
            out["vendor"].append(vendor)
            out["attach"].append(attach)
            out["insert"].append(insert)
            out["update"].append(update)
            out["total"].append(attach + insert + update)
        return out

    @staticmethod
    def summary_report(
        report_data: list[bibs.MatchAnalysis],
        library: str,
        collection: str,
        record_type: str,
        file_names: list[str],
    ) -> Any:
        return reports.SummaryReport(
            library=library,
            collection=collection,
            record_type=record_type,
            file_names=file_names,
            total_files_processed=len(file_names),
            total_records_processed=len(report_data),
            vendor_breakdown=ReportGenerator.vendor_breakdown(report_data=report_data),
        )
