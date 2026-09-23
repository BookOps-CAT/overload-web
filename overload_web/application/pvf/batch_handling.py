"""Application service commands for handling processed files."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import batch

logger = logging.getLogger(__name__)


class SaveProcessedFileBatch:
    @staticmethod
    def execute(
        batch_data: list[dict[str, Any]],
        file_names: list[str],
        repo: ports.SqlRepositoryProtocol,
        report_data: list[dict[str, Any]],
        missing_barcodes: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Save a batch of processed files and their associated processing stats.

        Args:
            batch_data: batches of files to be saved.
            file_names: the list of files processed as part of the workflow
            repo: a PVFBatchRepository where the processed file batch should be saved
            report_data: a `MatchAnalysis` object representing processing statistics
            missing barcodes: an optional list of barcodes missing from the output
        Returns:
            a list of filenames contained within the given directory as strings.
        """
        file_list = [
            batch.ProcessedFile(file_name=i["file_name"], records=i["records"])
            for i in batch_data
        ]
        processed_batch = batch.ProcessedFileBatch(
            files=file_list,
            stats=report_data,
            file_names=file_names,
            missing_barcodes=missing_barcodes,
        )
        return repo.save(processed_batch)
