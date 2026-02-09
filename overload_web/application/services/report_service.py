import logging

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class ReportGenerator:
    @staticmethod
    def processing_report(
        records: list[bibs.DomainBib],
    ) -> bibs.ProcessVendorFileReport:
        reports = []
        for record in records:
            if not record.analysis:
                raise ValueError("Bib record lacks processing report")
            reports.append(record.analysis)
        return bibs.ProcessVendorFileReport(reports)
