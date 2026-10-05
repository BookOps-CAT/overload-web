import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from overload_web.domain.pvf import services


@dataclass
class ProcessedFile:
    """A value object representing a processed file of MARC records"""

    file_name: str
    records: bytes


class ProcessedFileBatch:
    """A dataclass representing a batch of processed files and their statistics"""

    def __init__(
        self,
        stats: list[dict[str, Any]],
        file_names: list[str],
        files: list[ProcessedFile],
        missing_barcodes: list[str] | None = None,
    ) -> None:
        self.files = files
        self.stats = stats
        self.file_names = file_names
        self.total_files = len(file_names)
        self.total_records = len(stats)
        self.missing_barcodes = missing_barcodes
        self.processing_integrity = missing_barcodes in [[], None]


class AbstractProcessingJob(ABC):
    workflow_id: str
    vendor: str | None = None
    processed_files: list[ProcessedFile]
    report_data: list[dict[str, Any]]
    file_names: list[str]
    missing_barcodes: list[str]

    @abstractmethod
    def process(self, *args, **kwargs) -> None: ...  # pragma:no branch

    def create_batch(self) -> ProcessedFileBatch:
        return ProcessedFileBatch(
            files=self.processed_files,
            stats=self.report_data,
            file_names=self.file_names,
            missing_barcodes=self.missing_barcodes,
        )


class AcquisitionsSelectionJob(AbstractProcessingJob):
    """Aggregate Root representing a batch processing job for order-level workflow."""

    def __init__(self, workflow_id: str, vendor: str):
        self.workflow_id = workflow_id
        self.vendor = vendor

        self.file_names: list[str] = []
        self.missing_barcodes: list[str] = []
        self.processed_files: list[ProcessedFile] = []
        self.report_data: list[dict[str, Any]] = []
        self.validator = services.BarcodeValidator()

    def process(
        self,
        batches_data: dict[str, bytes],
        matcher: services.BibMatcher,
        matchpoints: dict[str, str],
        parser: services.BibParser,
        template_data: dict[str, Any],
        updater: services.BibUpdater,
    ) -> None:
        """The core domain logic loop."""

        for file_name, data in batches_data.items():
            self.file_names.append(file_name)
            records = parser.parse_marc_data(data=data, vendor=self.vendor)
            barcodes = self.validator.validate_unique([bib.barcodes for bib in records])
            for bib in records:
                matches = matcher.match_order_record(
                    record=bib, matchpoints=matchpoints
                )
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                updates = updater.get_order_level_updates(
                    record=bib, template_data=template_data
                )
                updater.apply_field_updates(record=bib, updates=updates)
                self.report_data.append(analysis.to_dict())
            self.validator.validate_preserved(
                original_barcodes=barcodes,
                processed_barcodes=[bib.barcodes for bib in records],
            )
            self.processed_files.append(
                ProcessedFile(file_name=file_name, records=parser.write(records))
            )


class CatalogingJob(AbstractProcessingJob):
    """Aggregate Root representing a batch processing job for cataloging workflow."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id

        self.file_names: list[str] = []
        self.missing_barcodes: list[str] = []
        self.processed_files: list[ProcessedFile] = []
        self.report_data: list[dict[str, Any]] = []
        self.out_file_name = datetime.datetime.today().strftime("%y%m%d")
        self.validator = services.BarcodeValidator()

    def process(
        self,
        batches_data: dict[str, bytes],
        matcher: services.BibMatcher,
        parser: services.BibParser,
        updater: services.BibUpdater,
    ) -> None:
        """The core domain logic loop."""
        reviewer = services.BibReviewer(handler=updater.handler)
        data_list = []
        for file_name, file_data in batches_data.items():
            self.file_names.append(file_name)
            data_list.append(file_data)
        data = parser.combine_marc_files(data_list)
        records = parser.parse_marc_data(data=data)
        barcodes = self.validator.validate_unique([bib.barcodes for bib in records])
        for bib in records:
            matches = matcher.match_full_record(bib)
            analysis = matcher.review_matches(bib=bib, matches=matches)
            bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
            updates = updater.get_full_record_updates(record=bib)
            updater.apply_field_updates(record=bib, updates=updates)
            self.report_data.append(analysis.to_dict())
        self.missing_barcodes.extend(
            self.validator.validate_preserved(
                original_barcodes=barcodes,
                processed_barcodes=[bib.barcodes for bib in records],
            )
        )
        reviewed = reviewer.review_batch(records=records)
        deduplicated = reviewer.deduplicate(reviewed)
        files = [
            ProcessedFile(
                file_name=f"{self.out_file_name}-{k}.mrc", records=parser.write(v)
            )
            for k, v in deduplicated.items()
        ]
        self.processed_files.extend(files)
