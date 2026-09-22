"""Application serivce commands for the process vendor file service."""

import datetime
import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.pvf import (
    file_handling,
    match_service,
    parsing_service,
    review_service,
    update_service,
)
from overload_web.domain.pvf import batch

logger = logging.getLogger(__name__)


class ProcessAcquisitionsRecords:
    """Parses, matches, and analyzes order-level MARC records for acquisitions."""

    @staticmethod
    def execute(
        workflow_id: str,
        storage: ports.FileStorage,
        fetcher: ports.BibFetcher,
        marc_updater: ports.MarcUpdaterPort,
        marc_parser: ports.MarcParserPort,
        update_rules: dict[str, Any],
        parsing_rules: parsing_service.ParsingRules,
        matchpoints: dict[str, str],
        repo: ports.SqlRepositoryProtocol,
        template_data: dict[str, Any],
        file_repo: ports.SqlRepositoryProtocol,
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
                a `ports.MarcParserPort` object used by the command.
            marc_updater:
                a `ports.MarcUpdaterPort` object used by the command.
            parsing_rules:
                a `ParsingRules` object containing cataloging rules for MARC parsing.
            update_rules:
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
        batches = file_handling.LoadAllWorkflowFiles.execute(
            workflow_id=workflow_id, storage=storage, repo=file_repo
        )
        matcher = match_service.BibMatcher(fetcher)
        parser = parsing_service.BibParser(rules=parsing_rules, handler=marc_parser)
        updater = update_service.BibUpdater(
            bib_id_tag=update_rules["bib_id_tag"],
            collection=update_rules["collection"],
            handler=marc_updater,
            default_loc=update_rules["default_loc"],
            library=update_rules["library"],
            order_mapping=update_rules["order_mapping"],
        )
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = parser.parse_marc_data(data=data, vendor=vendor)
            batch.BarcodeValidator.validate_unique(
                barcodes=[i.barcodes for i in records]
            )
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                updates = updater.get_acq_updates(bib, template_data=template_data)
                updater.apply_field_updates(record=bib, updates=updates)
                report_data.append(analysis.to_dict())
            processed = batch.ProcessedFile(
                file_name=file_name, records=marc_parser.write(records)
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
        workflow_id: str,
        storage: ports.FileStorage,
        fetcher: ports.BibFetcher,
        marc_updater: ports.MarcUpdaterPort,
        marc_parser: ports.MarcParserPort,
        update_rules: dict[str, Any],
        parsing_rules: parsing_service.ParsingRules,
        repo: ports.SqlRepositoryProtocol,
        file_repo: ports.SqlRepositoryProtocol,
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
                a `ports.MarcParserPort` object used by the command.
            marc_updater:
                a `ports.MarcUpdaterPort` object used by the command.
            parsing_rules:
                a `ParsingRules` object containing cataloging rules for MARC parsing.
            update_rules:
                a dictionary containing cataloging rules for MARC updates.
            repo:
                a `ports.SqlRepositoryProtocol` object used by the command.
        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
        """
        batches = file_handling.LoadAllWorkflowFiles.execute(
            workflow_id=workflow_id, storage=storage, repo=file_repo
        )
        file_names = list(batches.keys())
        content = list(batches.values())
        parser = parsing_service.BibParser(rules=parsing_rules, handler=marc_parser)
        data = parser.combine_marc_files(data=content)
        records = parser.parse_marc_data(data=data)
        original_barcodes = batch.BarcodeValidator.validate_unique(
            barcodes=[i.barcodes for i in records]
        )
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        updater = update_service.BibUpdater(
            bib_id_tag=update_rules["bib_id_tag"],
            collection=update_rules["collection"],
            handler=marc_updater,
            default_loc=update_rules["default_loc"],
            library=update_rules["library"],
            order_mapping=update_rules["order_mapping"],
        )
        for bib in records:
            matches = matcher.match_full_record(bib)
            analysis = matcher.review_matches(bib=bib, matches=matches)
            bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
            updates = updater.get_cat_updates(bib)
            updater.apply_field_updates(record=bib, updates=updates)
            report_data.append(analysis.to_dict())
        missing_barcodes = batch.BarcodeValidator.validate_preserved(
            processed_barcodes=[i.barcodes for i in records],
            original_barcodes=original_barcodes,
        )
        reviewer = review_service.BibReviewer(handler=marc_updater)
        deduplicated = reviewer.deduplicate(records=records)
        file_name = datetime.datetime.today().strftime("%y%m%d")
        files = [
            batch.ProcessedFile(
                file_name=f"{file_name}-{k}.mrc", records=marc_parser.write(v)
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
        workflow_id: str,
        storage: ports.FileStorage,
        fetcher: ports.BibFetcher,
        marc_updater: ports.MarcUpdaterPort,
        marc_parser: ports.MarcParserPort,
        update_rules: dict[str, Any],
        parsing_rules: parsing_service.ParsingRules,
        matchpoints: dict[str, str],
        repo: ports.SqlRepositoryProtocol,
        template_data: dict[str, Any],
        file_repo: ports.SqlRepositoryProtocol,
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
                a `ports.MarcParserPort` object used by the command.
            marc_updater:
                a `ports.MarcUpdaterPort` object used by the command.
            parsing_rules:
                a `ParsingRules` object containing cataloging rules for MARC parsing.
            update_rules:
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
        batches = file_handling.LoadAllWorkflowFiles.execute(
            workflow_id=workflow_id, storage=storage, repo=file_repo
        )
        out_batches = []
        file_names = []
        report_data = []
        matcher = match_service.BibMatcher(fetcher)
        updater = update_service.BibUpdater(
            bib_id_tag=update_rules["bib_id_tag"],
            collection=update_rules["collection"],
            handler=marc_updater,
            default_loc=update_rules["default_loc"],
            library=update_rules["library"],
            order_mapping=update_rules["order_mapping"],
        )
        parser = parsing_service.BibParser(rules=parsing_rules, handler=marc_parser)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = parser.parse_marc_data(data=data, vendor=vendor)
            batch.BarcodeValidator.validate_unique(
                barcodes=[i.barcodes for i in records]
            )
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                updates = updater.get_sel_updates(bib, template_data=template_data)
                updater.apply_field_updates(record=bib, updates=updates)
                report_data.append(analysis.to_dict())
            processed = batch.ProcessedFile(
                file_name=file_name, records=marc_parser.write(records)
            )
            out_batches.append(processed)
        processed_batch = batch.ProcessedFileBatch(
            files=out_batches, stats=report_data, file_names=file_names
        )
        return repo.save(processed_batch)
