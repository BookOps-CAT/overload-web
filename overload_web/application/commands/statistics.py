import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.models import bibs, reports

logger = logging.getLogger(__name__)


class CreateRecordsProcessingReport:
    @staticmethod
    def execute(
        processed: bibs.ProcessedMarcFile | list[bibs.ProcessedMarcFile],
        handler: ports.ReportHandler,
    ) -> reports.ProcessingStatistics:
        file_names = []
        missing_barcodes = []
        all_recs = []
        if isinstance(processed, list):
            for file in processed:
                file_names.append(file.file_name)
                missing_barcodes.extend(file.missing_barcodes)
                all_recs.extend(file.records)
        else:
            file_names.append(processed.file_name)
            missing_barcodes.extend(processed.missing_barcodes)
            all_recs.extend(processed.records)
        data_dict: dict[str, Any] = {
            "total_records_processed": len(all_recs),
            "file_names": file_names,
            "total_files_processed": len(file_names),
            "missing_barcodes": missing_barcodes,
        }
        data_dict.update(handler.list2dict(all_recs))
        return reports.ProcessingStatistics(**data_dict)


class WriteReportToSheet:
    @staticmethod
    def execute(
        report_data: reports.ProcessingStatistics,
        handler: ports.ReportHandler,
        writer: ports.ReportWriter,
    ) -> None:
        call_no_report = handler.create_call_number_report(report_data)
        if call_no_report:
            prepped_data = writer.prep_report(data=call_no_report)
            writer.write_report(prepped_data)
        duplicates_report = handler.create_duplicate_report(report_data)
        prepped_data = writer.prep_report(data=duplicates_report)
        writer.write_report(prepped_data)
