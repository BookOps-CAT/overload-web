import logging

from overload_web.domain.models import bibs, reports

logger = logging.getLogger(__name__)


class ReportGenerator:
    @staticmethod
    def processing_report(
        records: list[bibs.DomainBib], file_name: str
    ) -> reports.FileReport:
        report_data = []
        for record in records:
            if not record.analysis:
                raise ValueError("Bib record lacks processing report")
            report_data.append(record.analysis)
        return reports.FileReport(report_data, file_name=file_name)

    @staticmethod
    def session_report(
        analyses: dict[str, reports.FileReport],
        library: str,
        collection: str,
        record_type: str,
    ) -> reports.SessionReport:
        return reports.SessionReport(
            analyses=analyses,
            library=library,
            collection=collection,
            record_type=record_type,
        )
