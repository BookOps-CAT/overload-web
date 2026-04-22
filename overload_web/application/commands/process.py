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
        repo: ports.SqlRepositoryProtocol,
    ) -> dict[str, Any]:
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
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
        """
        data = marc_services.MarcFileMerger.combine_marc_files(
            data=[i for i in batches.values()], engine=marc_engine
        )
        records = marc_services.BibParser.parse_marc_data(data=data, engine=marc_engine)
        bibs.DomainBib.validate_unique_barcodes(records)
        barcodes = bibs.DomainBib.extract_barcodes(records)
        for bib in records:
            matches = match_service.BibMatcher(fetcher).match_full_record(bib)
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
            marc_services.BibUpdater.apply_full_record_updates(bib, engine=marc_engine)

        missing_barcodes = bibs.DomainBib.validate_preserved_barcodes(
            records=records, barcodes=barcodes
        )
        deduplicated = marc_services.BibDeduplicator.deduplicate(
            records=records, engine=marc_engine
        )
        file_name = datetime.datetime.today().strftime("%y%m%d")
        report = bibs.DomainBib.create_full_records_report(
            records=records,
            missing_barcodes=missing_barcodes,
            file_names=[i for i in batches.keys()],
        )
        files = [
            bibs.ProcessedFile(
                file_name=f"{file_name}-{k}.mrc", records=bibs.DomainBib.write(v)
            )
            for k, v in deduplicated.items()
        ]
        processed_batch = bibs.ProcessedFileBatch(files=files, report=report)
        return repo.save(processed_batch)


class ProcessOrderRecords:
    """Handles parsing, matching, and analysis of of order-level MARC records."""

    @staticmethod
    def execute(
        batches: dict[str, bytes],
        fetcher: ports.BibFetcher,
        marc_engine: ports.MarcEnginePort,
        matchpoints: dict[str, str],
        repo: ports.SqlRepositoryProtocol,
        template_data: dict[str, Any],
    ) -> dict[str, Any]:
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
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
            template_data:
                Order template data as a dictionary.
        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
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
            bibs.DomainBib.validate_unique_barcodes(records)
            for bib in records:
                matches = match_service.BibMatcher(fetcher).match_order_record(
                    bib, matchpoints=matchpoints
                )
                analysis = bib.analyze_matches(candidates=matches)
                bib.apply_match(analysis)
                marc_services.BibUpdater.apply_order_record_updates(
                    bib, engine=marc_engine, template_data=template_data
                )
            all_records.extend(records)
            out_batches.append(
                bibs.ProcessedFile(
                    file_name=file_name, records=bibs.DomainBib.write(records)
                )
            )
        report = bibs.DomainBib.create_order_records_report(
            records=all_records, file_names=file_names
        )
        processed_batch = bibs.ProcessedFileBatch(files=out_batches, report=report)
        return repo.save(processed_batch)
