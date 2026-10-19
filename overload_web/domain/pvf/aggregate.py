import datetime
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

from overload_web.domain.pvf import files, models, ports, services

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFile:
    """A value object representing a processed file of MARC records"""

    file_name: str
    records: bytes


@dataclass
class ProcessedFileBatch:
    """A dataclass representing a batch of processed files and their statistics"""

    file_names: list[str]
    files: list[ProcessedFile]
    stats: list[dict[str, Any]]
    missing_barcodes: list[str] | None = None

    @property
    def processing_integrity(self) -> bool:
        return self.missing_barcodes in [[], None]

    @property
    def total_files(self) -> int:
        return len(self.file_names)

    @property
    def total_records(self) -> int:
        return len(self.stats)


class AbstractProcessingJob(ABC):
    workflow_id: str
    vendor: str | None = None
    processed_files: list[ProcessedFile]
    report_data: list[dict[str, Any]]
    file_names: list[str]
    batches_data: dict[str, bytes]
    missing_barcodes: list[str]
    processed: ProcessedFileBatch | None

    def load_files(
        self, files: Sequence[files.IncomingFile], storage: ports.FileStorage
    ) -> None:
        self.batches_data = {i.filename: storage.load(i.reference) for i in files}

    @abstractmethod
    def parse_files(self, *args, **kwargs) -> None: ...  # pragma:no branch

    @abstractmethod
    def match_records(self, *args, **kwargs) -> None: ...  # pragma:no branch

    @abstractmethod
    def apply_updates_and_create_batch(
        self, *args, **kwargs
    ) -> None: ...  # pragma:no branch


class OrderLevelJob(AbstractProcessingJob):
    """Aggregate Root representing a batch processing job for order-level workflow."""

    def __init__(self, workflow_id: str, vendor: str):
        self.workflow_id = workflow_id
        self.vendor = vendor

        self.batches_data: dict[str, bytes] = {}
        self.file_names: list[str] = []
        self.file_records: dict[str, list[models.DomainBib]] = {}
        self.missing_barcodes: list[str] = []
        self.processed: ProcessedFileBatch | None = None
        self.processed_files: list[ProcessedFile] = []
        self.report_data: list[dict[str, Any]] = []
        self.validator = services.BarcodeValidator()

    def parse_files(self, parser: services.BibParser) -> None:
        for file_name, data in self.batches_data.items():
            self.file_names.append(file_name)
            parsed = parser.parse_marc_data(data=data, vendor=self.vendor)
            self.validator.validate_unique([bib.barcodes for bib in parsed])
            self.file_records[file_name] = parsed

    def match_records(
        self, matcher: services.BibMatcher, matchpoints: dict[str, str]
    ) -> None:
        for file_name, records in self.file_records.items():
            for bib in records:
                matches = matcher.match_order_record(
                    record=bib, matchpoints=matchpoints
                )
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                self.report_data.append(analysis.to_dict())

    def apply_updates_and_create_batch(
        self, template_data: dict[str, Any], updater: services.BibUpdater
    ) -> None:
        """The core domain logic loop."""
        for file_name, records in self.file_records.items():
            for bib in records:
                updates = updater.get_order_level_updates(
                    record=bib, template_data=template_data
                )
                updater.apply_field_updates(record=bib, updates=updates)
            out_binary = updater.write(records)
            self.processed_files.append(
                ProcessedFile(file_name=file_name, records=out_binary)
            )
        self.processed = ProcessedFileBatch(
            files=self.processed_files,
            stats=self.report_data,
            file_names=self.file_names,
            missing_barcodes=self.missing_barcodes,
        )


class FullRecordJob(AbstractProcessingJob):
    """Aggregate Root representing a batch processing job for cataloging workflow."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id

        self.batches_data: dict[str, bytes] = {}
        self.file_names: list[str] = []
        self.records: list[models.DomainBib] = []
        self.missing_barcodes: list[str] = []
        self.original_barcodes: list[str] = []
        self.processed: ProcessedFileBatch | None = None
        self.processed_files: list[ProcessedFile] = []
        self.report_data: list[dict[str, Any]] = []
        self.out_file_name = datetime.datetime.today().strftime("%y%m%d")
        self.validator = services.BarcodeValidator()

    def parse_files(self, parser: services.BibParser) -> None:
        data_list = []
        for file_name, file_data in self.batches_data.items():
            self.file_names.append(file_name)
            data_list.append(file_data)
        data = parser.combine_marc_files(data_list)
        records = parser.parse_marc_data(data=data)
        self.original_barcodes = self.validator.validate_unique(
            [bib.barcodes for bib in records]
        )
        self.records = records

    def match_records(self, matcher: services.BibMatcher) -> None:
        for bib in self.records:
            matches = matcher.match_full_record(bib)
            analysis = matcher.review_matches(bib=bib, matches=matches)
            bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
            self.report_data.append(analysis.to_dict())

    def apply_updates_and_create_batch(self, updater: services.BibUpdater) -> None:
        reviewer = services.BibReviewer(handler=updater.handler)
        for bib in self.records:
            updates = updater.get_full_record_updates(record=bib)
            updater.apply_field_updates(record=bib, updates=updates)
        self.missing_barcodes.extend(
            self.validator.validate_preserved(
                original_barcodes=self.original_barcodes,
                processed_barcodes=[bib.barcodes for bib in self.records],
            )
        )
        reviewed = reviewer.review_batch(records=self.records)
        deduplicated = reviewer.deduplicate(reviewed)
        for k, v in deduplicated.items():
            self.processed_files.append(
                ProcessedFile(
                    file_name=f"{self.out_file_name}-{k}.mrc", records=updater.write(v)
                )
            )
        self.processed = ProcessedFileBatch(
            files=self.processed_files,
            stats=self.report_data,
            file_names=self.file_names,
            missing_barcodes=self.missing_barcodes,
        )
