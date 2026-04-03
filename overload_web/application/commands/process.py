import datetime
import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.services import (
    marc_services,
    match_service,
    report_services,
)
from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class CombineMarcFiles:
    """Combine multiple MARC files into one for processing CAT records."""

    @staticmethod
    def execute(data: list[bytes], marc_engine: ports.MarcEnginePort) -> bytes:
        return marc_services.MarcFileMerger.combine_marc_files(
            data=data, engine=marc_engine
        )


class ProcessFullRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        data: bytes,
        file_names: list[str],
        marc_engine: ports.MarcEnginePort,
        fetcher: ports.BibFetcher,
    ) -> bibs.ProcessedFileBatch:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the match analysis.

        Args:
            data: binary MARC data as a `bytes` object.
            file_names: the list of files being processed.
            marc_engine: a `ports.MarcEnginePort` object used by the command.
            fetcher: a `ports.BibFetcher` object used by the command.
        Returns:
            A `ProcessedFileBatch` object containing the processed records as bytes
            objects and the processing statistics
        """
        records = marc_services.BibParser.parse_marc_data(data=data, engine=marc_engine)
        marc_services.BarcodeValidator.ensure_unique(records)
        barcodes = marc_services.BarcodeExtractor.extract_barcodes(records)
        for bib in records:
            matches = match_service.BibMatcher(fetcher).match_full_record(bib)
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
            marc_services.BibUpdater.update_record(bib, engine=marc_engine)

        missing_barcodes = marc_services.BarcodeValidator.ensure_preserved(
            records=records, barcodes=barcodes
        )
        deduplicated = marc_services.Deduplicator.deduplicate(
            records=records, engine=marc_engine
        )
        file_name = datetime.datetime.today().strftime("%y%m%d")
        report = report_services.PVFReporter.create_full_records_report(
            records=records, missing_barcodes=missing_barcodes, file_names=file_names
        )
        files = [
            bibs.ProcessedFile(
                file_name=f"{file_name}-{k}.mrc",
                content=marc_services.BibSerializer.write(v),
            )
            for k, v in deduplicated.items()
        ]
        return bibs.ProcessedFileBatch(files=files, report=report)


class SaveProcessedRecords:
    @staticmethod
    def execute(
        repo: ports.SqlRepositoryProtocol, batch: bibs.ProcessedFileBatch
    ) -> dict[str, Any]:
        return repo.save(batch)


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
                marc_services.BibUpdater.update_record(
                    bib, engine=marc_engine, template_data=template_data
                )
            all_records.extend(records)
            out_batches.append(
                bibs.ProcessedFile(
                    file_name=file_name,
                    content=marc_services.BibSerializer.write(records),
                )
            )
        report = report_services.PVFReporter.create_order_records_report(
            records=all_records, file_names=file_names
        )
        return bibs.ProcessedFileBatch(files=out_batches, report=report)
