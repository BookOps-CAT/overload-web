import logging

from overload_web.application import ports
from overload_web.domain.models import record_batches, reports

logger = logging.getLogger(__name__)


class CreateFullRecordsProcessingReport:
    @staticmethod
    def execute(
        processed: record_batches.ProcessedFullMarcFile,
        file_names: list[str],
        handler: ports.ReportHandler,
    ) -> reports.ProcessingStatistics:
        all_recs = processed.merge_records + processed.insert_records
        missing_barcodes = processed.missing_barcodes
        data_dict = handler.list2dict(all_recs)
        integrity = missing_barcodes != []
        return reports.ProcessingStatistics(
            file_names=file_names,
            total_files_processed=len(file_names),
            total_records_processed=len(all_recs),
            missing_barcodes=missing_barcodes,
            processing_integrity=integrity,
            detailed_data=data_dict,
            vendor_breakdown=handler.create_vendor_report(data_dict),
            duplicates_report=handler.create_duplicate_report(data_dict),
            call_number_issues=handler.create_call_number_report(data_dict),
        )


class CreateOrderRecordsProcessingReport:
    @staticmethod
    def execute(
        report_data: list[record_batches.ProcessedOrderMarcFile],
        handler: ports.ReportHandler,
    ) -> reports.OrderProcessingStatistics:
        file_names = [i.file_name for i in report_data]
        all_recs = []
        for report in report_data:
            all_recs.extend(report.records)
        data_dict = handler.list2dict(all_recs)
        return reports.OrderProcessingStatistics(
            summary=handler.create_summary_report(
                file_names=file_names,
                total_records_processed=len(all_recs),
                report_data=data_dict,
            ),
            detailed_data=data_dict,
        )


class WriteReportToSheet:
    @staticmethod
    def execute(
        report_data: reports.OrderProcessingStatistics, handler: ports.ReportHandler
    ) -> None:
        call_no_report = report_data.summary["call_number_issues"]
        if call_no_report:
            prepped_data = handler.prep_report(data=call_no_report)
            handler.write_report(prepped_data)
        duplicates_report = report_data.summary["duplicates_report"]
        if duplicates_report:
            prepped_data = handler.prep_report(data=duplicates_report)
            handler.write_report(prepped_data)
