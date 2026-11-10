"""Application service commands for reporting operations."""

import logging
from typing import Any

from overload_web.domain.pvf import ports

logger = logging.getLogger(__name__)


class WriteOutputReport:
    """Write processing statistics to a google sheet."""

    @staticmethod
    def execute(report_data: dict[str, Any], writer: ports.ReportWriter) -> None:
        """Execute `WriteOutputReport` command.

        Args:
            report_data:
                Processing statistics for a workflow as a dictionary.
            writer:
                a `ports.ReportWriter` object used by the command.

        Returns:
            The report data as a dictionary.

        """
        call_no_report = report_data.get("call_number_report")
        if call_no_report:
            prepped_data = writer.prep_report(data=call_no_report)
            writer.write_report(prepped_data)
        prepped_data = writer.prep_report(data=report_data["duplicate_report"])
        writer.write_report(prepped_data)
