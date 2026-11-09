"""Domain aggregates and related objects for process vendor file workflow."""

import datetime
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from overload_web.domain.pvf import files, models, ports, services

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFile:
    """A value object representing a processed file of MARC records."""

    file_name: str
    records: bytes


@dataclass
class ProcessedFileBatch:
    """A dataclass representing a batch of processed files and their statistics."""

    file_names: list[str]
    files: list[ProcessedFile]
    stats: list[dict[str, Any]]
    missing_barcodes: list[str] | None = None

    @property
    def processing_integrity(self) -> bool:
        """Whether or not the batch of processed files is missing barcodes."""
        return self.missing_barcodes in [[], None]

    @property
    def total_files(self) -> int:
        """Total number of files processed."""
        return len(self.file_names)

    @property
    def total_records(self) -> int:
        """Total number of records processed."""
        return len(self.stats)


class AbstractProcessingJob(ABC):  # pragma: no branch
    """Abstract base class for the aggregate root."""

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
        """Load a list of `IncomingFiles` objects from a `FileStorage` location.

        Args:
            files: a list of `IncomingFiles` objects
            storage: the `ports.FileStorage` object where the files will be loaded from

        Returns:
            None. Assigns the loaded files as a dictionary of string/bytes object pairs
            to the `batches_data` attribute of the class instance.

        """
        self.batches_data = {i.filename: storage.load(i.reference) for i in files}

    @abstractmethod
    def parse_files(self, *args: Any, **kwargs: Any) -> None:
        """Parse the contents of a list of files into `DomainBib` domain objects."""
        ...

    @abstractmethod
    def match_records(self, *args: Any, **kwargs: Any) -> None:
        """Match parsed records against records in Sierra."""
        ...

    @abstractmethod
    def apply_updates_and_create_batch(self, *args: Any, **kwargs: Any) -> None:
        """Apply appropriate updates and output processed records to MARC."""
        ...


class OrderLevelJob(AbstractProcessingJob):
    """Aggregate Root representing a batch job for an order-level processing workflow.

    Attributes:
        batches_data:
            a dictionary containing each file's name and contents as string/bytes pairs
        file_names:
            a list containing the names of all files being processed by the workflow
        file_records:
            a dictionary containing each file's name and its parsed contents as a list
            of `DomainBib` domain objects
        missing_barcodes:
            a list of barcodes as strings present in the original files but not present
            in the processed output files
        processed:
            a `ProcessedFileBatch` object representing the the output of the workflow
        processed_files:
            a list of `ProcessedFile` objects
        report_data:
            a list of dictionaries containing processing statistics
        vendor:
            a string representing the vendor associated with the workflow
        workflow_id:
            the unique ID for the job's workflow as a string

    """

    def __init__(self, workflow_id: str, vendor: str) -> None:
        """Initialize an order-level processing job.

        Args:
            vendor: the vendor whose records are being processed by the workflow
            workflow_id: the workflow whose files are being processed

        """
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

    def parse_files(
        self,
        library: str,
        parser: services.BibParser,
        record_type: str,
        vendor: str | None,
    ) -> None:
        """Parse the contents of a list of files into `DomainBib` domain objects.

        Args:
            library: the library whose records are being processed as a string
            parser: a `BibParser` application service with an injected `MarcParser`
            record_type: the record_type (`acq` or `sel`) for the workflow as a string
            vendor: the vendor whose records are being parsed and processed

        Returns:
            None. The files being processed are assigned to the `file_names` attribute
            as a list of strings. The parsed records (as a dictionary containing each
            file's name and its parsed contents as `DomainBib` domain objects) are
            assigned to the `file_records` attribute of the class instance.

        """
        for file_name, data in self.batches_data.items():
            self.file_names.append(file_name)
            parsed = parser.parse_marc_data(
                library=library, record_type=record_type, data=data, vendor=vendor
            )
            self.validator.validate_unique([bib.barcodes for bib in parsed])
            self.file_records[file_name] = parsed

    def match_records(
        self, library: str, matcher: services.BibMatcher, matchpoints: dict[str, str]
    ) -> None:
        """Match each record in the workflow against Sierra and analyse the matches.

        Each `DomainBib` object is searched against Sierra using each matchpoint
        until the catalog successfully returns a list of matches. The results returned
        by the `BibMatcher` are then analyzed and the best match is identified by a
        `MatchAnalyzer` object before updating the `DomainBib` with the matched bib_id
        and catalog action, as appropriate.

        Args:
            library: the library whose records are being processed as a string
            matcher: a `BibMatcher` application service with an injected `BibFetcher`
            matchpoints: a dictionary containing matchpoints to be used during matching

        Returns:
            None. The results of the matching process are saved to the `report_data`
            attribute of the class instance and the bib_id and cataloging action are
            assigned to each `DomainBib` object.

        """
        for records in self.file_records.values():
            for bib in records:
                matches = matcher.match_order_record(
                    record=bib, matchpoints=matchpoints, library=library
                )
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                self.report_data.append(analysis.to_dict())

    def apply_updates_and_create_batch(
        self,
        collection: str | None,
        library: str,
        record_type: str,
        template_data: dict[str, Any],
        updater: services.BibUpdater,
    ) -> None:
        """Update `DomainBib` objects with appropriate MARC fields and output to MARC.

        Args:
            collection:
                the collection (`'BL'` or `'RL'`) whose records are being
                processed as a string
            library:
                the library whose records are being processed as a string
            record_type:
                the record_type (`acq` or `sel`) for the workflow as a string
            template_data:
                the order template data to be applied to the processed records.
            updater:
                a `BibUpdater` application service with an injected `MarcUpdater`.

        Returns:
            None. The domain objects are converted to MARC records, appropriate
            fields are added, and the files are writen to a bytes objects before
            being assigned to the `processed_files` attribute as a list of
            `ProcessedFile` objects. The processed files and their processing
            statistics are then assigned to the `processed` attribute as a
            `ProcessedFileBatch` object.

        """
        for file_name, records in self.file_records.items():
            for bib in records:
                updates = updater.get_order_level_updates(
                    collection=collection,
                    library=library,
                    record_type=record_type,
                    record=bib,
                    template_data=template_data,
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
    """Aggregate Root representing a batch job for a full-level processing workflow.

    Attributes:
        batches_data:
            a dictionary containing each file's name and contents as string/bytes pairs
        file_names:
            a list containing the names of all files being processed by the workflow
        records:
            a list of `DomainBib` domain objects representing the combined and parsed
            contents of each file
        missing_barcodes:
            a list of barcodes as strings present in the original files but not present
            in the processed output files
        original_barcodes:
            a the list of barcodes as strings present in the original files
        processed:
            a `ProcessedFileBatch` object representing the the output of the workflow
        processed_files:
            a list of `ProcessedFile` objects
        report_data:
            a list of dictionaries containing processing statistics
        workflow_id:
            the unique ID for the job's workflow as a string

    """

    def __init__(self, workflow_id: str) -> None:
        """Initialize an cataloging/full-level MARC record processing job.

        Args:
            workflow_id: the workflow whose files are being processed

        """
        self.workflow_id = workflow_id

        self.batches_data: dict[str, bytes] = {}
        self.file_names: list[str] = []
        self.records: list[models.DomainBib] = []
        self.missing_barcodes: list[str] = []
        self.original_barcodes: list[str] = []
        self.processed: ProcessedFileBatch | None = None
        self.processed_files: list[ProcessedFile] = []
        self.report_data: list[dict[str, Any]] = []
        self.out_file_name = datetime.datetime.now(tz=datetime.UTC).strftime("%y%m%d")
        self.validator = services.BarcodeValidator()

    def parse_files(
        self, library: str, parser: services.BibParser, record_type: str
    ) -> None:
        """Parse the contents of a list of files into `DomainBib` domain objects.

        Args:
            library: the library whose records are being processed as a string
            parser: a `BibParser` application service with an injected `MarcParser`
            record_type: the record_type (`cat`) for the workflow as a string
            vendor: not used by method but used by method of base class
        Returns:
            None. The files being processed are assigned to the `file_names` attribute
            as a list of strings, the parsed records as a list of `DomainBib` domain
            objects are assigned to the `records` attribute of the class instance,
            and the barcodes present in the original files as a list of strings are
            assigned to the `original_barcodes` attribute.

        """
        data_list = []
        for file_name, file_data in self.batches_data.items():
            self.file_names.append(file_name)
            data_list.append(file_data)
        data = parser.combine_marc_files(data=data_list, library=library)
        records = parser.parse_marc_data(
            data=data, library=library, record_type=record_type
        )
        self.original_barcodes = self.validator.validate_unique(
            [bib.barcodes for bib in records]
        )
        self.records = records

    def match_records(self, library: str, matcher: services.BibMatcher) -> None:
        """Match each record in the workflow against Sierra and analyse the matches.

        Each `DomainBib` object is searched against Sierra using each matchpoint
        until the catalog successfully returns a list of matches. The matchpoints
        are stored with the `DomainBib` object's `vendor_info` attribute. The results
        returned by the `BibMatcher` are then analyzed and the best match is identified
        by a `MatchAnalyzer` object before updating the `DomainBib` with the matched
        bib_id and catalog action, as appropriate.

        Args:
            library: the library whose records are being processed as a string
            matcher: a `BibMatcher` application service with an injected `BibFetcher`

        Returns:
            None. The results of the matching process are saved to the `report_data`
            attribute of the class instance and the bib_id and cataloging action are
            assigned to each `DomainBib` object.

        """
        for bib in self.records:
            matches = matcher.match_full_record(record=bib, library=library)
            analysis = matcher.review_matches(bib=bib, matches=matches)
            bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
            self.report_data.append(analysis.to_dict())

    def apply_updates_and_create_batch(
        self, collection: str | None, library: str, updater: services.BibUpdater
    ) -> None:
        """Update `DomainBib` objects with appropriate MARC fields and output to MARC.

        Args:
            collection:
                the collection (`'BL'` or `'RL'`) whose records are being
                processed as a string
            library:
                the library whose records are being processed as a string
            updater:
                a `BibUpdater` application service with an injected `MarcUpdater`.

        Returns:
            None. The domain objects are converted to MARC records, appropriate
            fields are added, and the files are writen to a bytes objects before
            being assigned to the `processed_files` attribute as a list of
            `ProcessedFile` objects. The processed files and their processing
            statistics are then assigned to the `processed` attribute as a
            `ProcessedFileBatch` object. If barcodes are identified as missing
            during this step they are assigned to the `missing_barcodes` attribute.

        """
        reviewer = services.BibReviewer(handler=updater.handler)
        for bib in self.records:
            updates = updater.get_full_record_updates(
                record=bib, collection=collection, library=library
            )
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
