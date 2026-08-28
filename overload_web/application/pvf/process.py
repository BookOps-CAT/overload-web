"""Application serivce commands for the process vendor file service."""

import datetime
import itertools
import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.pvf import marc, match_service
from overload_web.domain.pvf import bibs

logger = logging.getLogger(__name__)


def extract_nested_list(list_items: list[Any]) -> list[str]:
    """Extract all barcodes from a list of `DomainBib` objects"""
    return list(itertools.chain.from_iterable(list_items))


class ProcessAcquisitionsRecords:
    """Parses, matches, and analyzes order-level MARC records for acquisitions."""

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

        out_batches = []
        file_names = []
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc.BibParser.parse_marc_data(
                data=data, engine=marc_engine, vendor=vendor
            )
            original_barcodes = extract_nested_list([i.barcodes for i in records])
            marc.BarcodeValidator.validate_unique_barcodes(original_barcodes)
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = bib.analyze_matches(candidates=matches)
                bib.apply_match(analysis)
                marc.BibUpdater.update_acq_record(
                    bib, engine=marc_engine, template_data=template_data
                )
                report_data.append(analysis.to_dict())
            processed = bibs.ProcessedFile(
                file_name=file_name, records=marc_engine.write(records)
            )
            out_batches.append(processed)
        processed_batch = bibs.ProcessedFileBatch(
            files=out_batches, processing_statistics=report_data, file_names=file_names
        )
        return repo.save(processed_batch)


class ProcessCatalogingRecords:
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
        file_names = list(batches.keys())
        content = list(batches.values())
        data = marc.MarcFileMerger.combine_marc_files(data=content, engine=marc_engine)
        records = marc.BibParser.parse_marc_data(data=data, engine=marc_engine)
        original_barcodes = extract_nested_list([i.barcodes for i in records])
        marc.BarcodeValidator.validate_unique_barcodes(original_barcodes)
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        for bib in records:
            matches = matcher.match_full_record(bib)
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
            marc.BibUpdater.update_cat_record(bib, engine=marc_engine)
            report_data.append(analysis.to_dict())
        processed_barcodes = extract_nested_list([i.barcodes for i in records])
        missing_barcodes = marc.BarcodeValidator.validate_preserved_barcodes(
            processed_barcodes=processed_barcodes, original_barcodes=original_barcodes
        )
        deduplicated = marc.BibDeduplicator.deduplicate(
            records=records, engine=marc_engine
        )
        file_name = datetime.datetime.today().strftime("%y%m%d")
        files = [
            bibs.ProcessedFile(
                file_name=f"{file_name}-{k}.mrc", records=marc_engine.write(v)
            )
            for k, v in deduplicated.items()
        ]
        processed_batch = bibs.ProcessedFileBatch(
            files=files,
            processing_statistics=report_data,
            file_names=file_names,
            missing_barcodes=missing_barcodes,
        )
        return repo.save(processed_batch)


class ProcessSelectionRecords:
    """Parses, matches, and analyzes order-level MARC records for selection."""

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

        out_batches = []
        file_names = []
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc.BibParser.parse_marc_data(
                data=data, engine=marc_engine, vendor=vendor
            )
            original_barcodes = extract_nested_list([i.barcodes for i in records])
            marc.BarcodeValidator.validate_unique_barcodes(original_barcodes)
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = bib.analyze_matches(candidates=matches)
                bib.apply_match(analysis)
                marc.BibUpdater.update_sel_record(
                    bib, engine=marc_engine, template_data=template_data
                )
                report_data.append(analysis.to_dict())
            processed = bibs.ProcessedFile(
                file_name=file_name, records=marc_engine.write(records)
            )
            out_batches.append(processed)
        processed_batch = bibs.ProcessedFileBatch(
            files=out_batches, processing_statistics=report_data, file_names=file_names
        )
        return repo.save(processed_batch)
