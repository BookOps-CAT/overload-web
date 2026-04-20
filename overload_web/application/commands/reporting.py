import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.services import report_services

logger = logging.getLogger(__name__)


class CreatePVFOutputReport:
    @staticmethod
    def execute(
        batch_id: str,
        handler: ports.ReportHandler,
        repo: ports.SqlRepositoryProtocol,
        record_type: str,
    ) -> dict[str, list[Any]]:
        data = repo.get(batch_id)
        if data:
            report = report_services.PVFReporter.create_output_report(
                data=data["report"], handler=handler, record_type=record_type
            )
            return dict(report)
        return {}


class GetDetailedReportData:
    @staticmethod
    def execute(
        batch_id: str, handler: ports.ReportHandler, repo: ports.SqlRepositoryProtocol
    ) -> dict[str, list[Any]]:
        data = repo.get(batch_id)
        if data:
            report = report_services.PVFReporter.create_detailed_report(
                data=data["report"], handler=handler
            )
            return dict(report)
        return {}


class WriteOutputReport:
    @staticmethod
    def execute(
        batch_id: str,
        handler: ports.ReportHandler,
        repo: ports.SqlRepositoryProtocol,
        writer: ports.ReportWriter,
        record_type: str,
    ) -> None:
        data = repo.get(batch_id)
        if data:
            report_services.ReportWriter.write_report_to_google_sheet(
                data=data["report"],
                handler=handler,
                writer=writer,
                record_type=record_type,
            )
