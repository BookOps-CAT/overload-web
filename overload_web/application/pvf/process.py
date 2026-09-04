"""Application serivce commands for the process vendor file service."""

import datetime
import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.pvf import marc, match_service, update
from overload_web.domain.pvf import batch

logger = logging.getLogger(__name__)


class ProcessAcquisitionsRecords:
    """Parses, matches, and analyzes order-level MARC records for acquisitions."""

    @staticmethod
    def execute(
        batches: dict[str, bytes],
        fetcher: ports.BibFetcher,
        marc_handler: ports.MarcUpdateHandlerPort,
        marc_parser: ports.MarcParsingHandlerPort,
        marc_update_rules: dict[str, Any],
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
            marc_parser:
                a `ports.MarcParsingHandlerPort` object used by the command.
            marc_handler:
                a `ports.MarcUpdateHandlerPort` object used by the command.
            marc_update_rules:
                a dictionary containing cataloging rules for MARC updates.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
            template_data:
                order template data as a dictionary.
        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
        """

        out_batches = []
        file_names = []
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        updater = update.BibUpdater(**marc_update_rules)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc.BibParser.parse_marc_data(
                parser=marc_parser, data=data, vendor=vendor
            )
            batch.BarcodeValidator.validate_unique(records=records)
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(
                    target_bib_id=analysis.target_bib_id, action=analysis.action
                )
                update_fields = updater.get_acq_updates(
                    bib, template_data=template_data
                )
                updater.update_record(bib, handler=marc_handler, updates=update_fields)
                report_data.append(analysis.to_dict())
            processed = batch.ProcessedFile(
                file_name=file_name, records=marc_parser.reader.write(records)
            )
            out_batches.append(processed)
        processed_batch = batch.ProcessedFileBatch(
            files=out_batches, stats=report_data, file_names=file_names
        )
        return repo.save(processed_batch)


class ProcessCatalogingRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        batches: dict[str, bytes],
        fetcher: ports.BibFetcher,
        marc_handler: ports.MarcUpdateHandlerPort,
        marc_parser: ports.MarcParsingHandlerPort,
        marc_update_rules: dict[str, Any],
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
            fetcher:
                a `ports.BibFetcher` object used by the command.
            marc_parser:
                a `ports.MarcParsingHandlerPort` object used by the command.
            marc_handler:
                a `ports.MarcUpdateHandlerPort` object used by the command.
            marc_update_rules:
                a dictionary containing cataloging rules for MARC updates.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
        """
        file_names = list(batches.keys())
        content = list(batches.values())
        data = marc.BibParser.combine_marc_files(data=content, marc_handler=marc_parser)
        records = marc.BibParser.parse_marc_data(parser=marc_parser, data=data)
        original_barcodes = batch.BarcodeValidator.validate_unique(records=records)
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        updater = update.BibUpdater(**marc_update_rules)
        for bib in records:
            matches = matcher.match_full_record(bib)
            analysis = matcher.review_matches(bib=bib, matches=matches)
            bib.apply_match(
                target_bib_id=analysis.target_bib_id, action=analysis.action
            )
            update_fields = updater.get_cat_updates(bib)
            updater.update_record(bib, handler=marc_handler, updates=update_fields)
            report_data.append(analysis.to_dict())
        missing_barcodes = batch.BarcodeValidator.validate_preserved(
            processed_records=records, original_barcodes=original_barcodes
        )
        deduplicated = marc.BibDeduplicator.deduplicate(
            records=records, handler=marc_handler
        )
        file_name = datetime.datetime.today().strftime("%y%m%d")
        files = [
            batch.ProcessedFile(
                file_name=f"{file_name}-{k}.mrc", records=marc_parser.reader.write(v)
            )
            for k, v in deduplicated.items()
        ]
        processed_batch = batch.ProcessedFileBatch(
            files=files,
            stats=report_data,
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
        marc_handler: ports.MarcUpdateHandlerPort,
        marc_parser: ports.MarcParsingHandlerPort,
        matchpoints: dict[str, str],
        marc_update_rules: dict[str, Any],
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
            marc_parser:
                a `ports.MarcParsingHandlerPort` object used by the command.
            marc_handler:
                a `ports.MarcUpdateHandlerPort` object used by the command.
            marc_update_rules:
                a dictionary containing cataloging rules for MARC updates.
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
        updater = update.BibUpdater(**marc_update_rules)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc.BibParser.parse_marc_data(
                parser=marc_parser, data=data, vendor=vendor
            )
            batch.BarcodeValidator.validate_unique(records=records)
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(
                    target_bib_id=analysis.target_bib_id, action=analysis.action
                )
                update_fields = updater.get_sel_updates(
                    record=bib, template_data=template_data
                )
                updater.update_record(bib, handler=marc_handler, updates=update_fields)
                report_data.append(analysis.to_dict())
            processed = batch.ProcessedFile(
                file_name=file_name, records=marc_parser.reader.write(records)
            )
            out_batches.append(processed)
        processed_batch = batch.ProcessedFileBatch(
            files=out_batches, stats=report_data, file_names=file_names
        )
        return repo.save(processed_batch)
