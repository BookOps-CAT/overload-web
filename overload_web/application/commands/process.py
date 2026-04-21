"""Application serivce commands for the process vendor file service."""

import datetime
import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.services import marc_services, match_service
from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class ProcessFullRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        batches: dict[str, bytes],
        marc_engine: ports.MarcEnginePort,
        fetcher: ports.BibFetcher,
    ) -> bibs.ProcessedFileBatch:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the match analysis.

        Args:
            batches:
                a dictionary containing pairs of file names and associated binary data
            marc_engine:
                a `ports.MarcEnginePort` object used by the command.
            fetcher:
                a `ports.BibFetcher` object used by the command.
        Returns:
            A `ProcessedFileBatch` object containing the processed records as bytes
            objects and the processing statistics
        """
        data = marc_services.MarcFileMerger.combine_marc_files(
            data=[i for i in batches.values()], engine=marc_engine
        )
        records = marc_services.BibParser.parse_marc_data(data=data, engine=marc_engine)
        marc_services.BarcodeValidator.ensure_unique(records)
        barcodes = marc_services.BarcodeExtractor.extract_barcodes(records)
        for bib in records:
            matches = match_service.BibMatcher(fetcher).match_full_record(bib)
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
            marc_services.BibUpdatePolicy.apply_full_record_updates(
                bib, engine=marc_engine
            )

        missing_barcodes = marc_services.BarcodeValidator.ensure_preserved(
            records=records, barcodes=barcodes
        )
        deduplicated = marc_services.BibDeduplicator.deduplicate(
            records=records, engine=marc_engine
        )
        file_name = datetime.datetime.today().strftime("%y%m%d")
        report = marc_services.PVFReporter.create_full_records_report(
            records=records,
            missing_barcodes=missing_barcodes,
            file_names=[i for i in batches.keys()],
        )
        files = [
            bibs.ProcessedFile(
                file_name=f"{file_name}-{k}.mrc",
                records=marc_services.BibSerializer.write(v),
            )
            for k, v in deduplicated.items()
        ]
        return bibs.ProcessedFileBatch(files=files, report=report)


class ProcessOrderRecords:
    """Handles parsing, matching, and analysis of of order-level MARC records."""

    @staticmethod
    def execute(
        batches: dict[str, bytes],
        fetcher: ports.BibFetcher,
        marc_engine: ports.MarcEnginePort,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
    ) -> bibs.ProcessedFileBatch:
        """
        Process order-level MARC records.

        This service parses order-level MARC records, matches them against Sierra,
        analyzes all bibs that were returned as matches, updates the records with
        required fields, and outputs the updated records and the match analysis.

        Args:
            batches:
                a dictionary containing pairs of file names and associated binary data
            fetcher:
                a `ports.BibFetcher` object used by the command.
            marc_engine:
                a `ports.MarcEnginePort` object used by the command.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.
        Returns:
            A `ProcessedFileBatch` object containing the processed records as bytes
            objects and the processing statistics
        """
        all_records = []
        out_batches = []
        file_names = []
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc_services.BibParser.parse_marc_data(
                data=data,
                engine=marc_engine,
                vendor=template_data.get("vendor", "UNKNOWN"),
            )
            marc_services.BarcodeValidator.ensure_unique(records)
            for bib in records:
                matches = match_service.BibMatcher(fetcher).match_order_record(
                    bib, matchpoints=matchpoints
                )
                analysis = bib.analyze_matches(candidates=matches)
                bib.apply_match(analysis)
                marc_services.BibUpdatePolicy.apply_order_record_updates(
                    bib, engine=marc_engine, template_data=template_data
                )
            all_records.extend(records)
            out_batches.append(
                bibs.ProcessedFile(
                    file_name=file_name,
                    records=marc_services.BibSerializer.write(records),
                )
            )
        report = marc_services.PVFReporter.create_order_records_report(
            records=all_records, file_names=file_names
        )
        return bibs.ProcessedFileBatch(files=out_batches, report=report)


class SaveProcessedRecords:
    @staticmethod
    def execute(
        batch: bibs.ProcessedFileBatch, repo: ports.SqlRepositoryProtocol
    ) -> dict[str, Any]:
        """
        Save a batch of processed records and processing statistics to local storage.

        Args:
            batch:
                A batch of processed records and their processing statistics as a
                `ProcessedFileBatch` object.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
        Returns:
            The processed record data and statistics as a dictionary.
        """
        return repo.save(batch)
