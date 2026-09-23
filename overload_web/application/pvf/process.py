"""Application serivce commands for the process vendor file service."""

import datetime
import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.pvf import (
    batch_handling,
    file_handling,
    marc,
    match_service,
    parsing_service,
    review_service,
    update_service,
)

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
        update_rules: update_service.UpdateRules,
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
        marc_handler = marc.MarcServiceHandler(
            parser=parsing_service.BibParser(rules=parsing_rules, handler=marc_parser),
            updater=update_service.BibUpdater(handler=marc_updater, rules=update_rules),
        )
        matcher = match_service.BibMatcher(fetcher)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc_handler.parse_and_validate_incoming(data=data, vendor=vendor)
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                marc_handler.apply_updates_by_record_type(
                    record=bib, record_type="acq", template_data=template_data
                )
                report_data.append(analysis.to_dict())
            processed = {"file_name": file_name, "records": marc_parser.write(records)}
            out_batches.append(processed)
        saved_batch = batch_handling.SaveProcessedFileBatch.execute(
            batch_data=out_batches,
            file_names=file_names,
            report_data=report_data,
            repo=repo,
        )
        return saved_batch


class ProcessCatalogingRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        workflow_id: str,
        storage: ports.FileStorage,
        fetcher: ports.BibFetcher,
        marc_updater: ports.MarcUpdaterPort,
        marc_parser: ports.MarcParserPort,
        update_rules: update_service.UpdateRules,
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
        report_data = []
        batches = file_handling.LoadAllWorkflowFiles.execute(
            workflow_id=workflow_id, storage=storage, repo=file_repo
        )
        file_names = list(batches.keys())
        content = list(batches.values())
        marc_handler = marc.MarcServiceHandler(
            parser=parsing_service.BibParser(rules=parsing_rules, handler=marc_parser),
            updater=update_service.BibUpdater(handler=marc_updater, rules=update_rules),
        )
        records = marc_handler.parse_and_validate_incoming(data=content)
        barcodes = marc_handler.extract_barcodes(records)
        matcher = match_service.BibMatcher(fetcher)
        for bib in records:
            matches = matcher.match_full_record(bib)
            analysis = matcher.review_matches(bib=bib, matches=matches)
            bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
            marc_handler.apply_updates_by_record_type(record=bib, record_type="cat")
            report_data.append(analysis.to_dict())
        missing_barcodes = marc_handler.validate_output(
            barcodes=barcodes, processed_recs=records
        )
        reviewer = review_service.BibReviewer(handler=marc_updater)
        deduplicated = reviewer.deduplicate(records=records)
        file_name = datetime.datetime.today().strftime("%y%m%d")
        files = [
            {"file_name": f"{file_name}-{k}.mrc", "records": marc_parser.write(v)}
            for k, v in deduplicated.items()
        ]
        saved_batch = batch_handling.SaveProcessedFileBatch.execute(
            batch_data=files,
            file_names=file_names,
            report_data=report_data,
            repo=repo,
            missing_barcodes=missing_barcodes,
        )
        return saved_batch


class ProcessSelectionRecords:
    """Parses, matches, and analyzes order-level MARC records for selection."""

    @staticmethod
    def execute(
        workflow_id: str,
        storage: ports.FileStorage,
        fetcher: ports.BibFetcher,
        marc_updater: ports.MarcUpdaterPort,
        marc_parser: ports.MarcParserPort,
        update_rules: update_service.UpdateRules,
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
        out_batches = []
        file_names = []
        report_data = []
        batches = file_handling.LoadAllWorkflowFiles.execute(
            workflow_id=workflow_id, storage=storage, repo=file_repo
        )
        marc_handler = marc.MarcServiceHandler(
            parser=parsing_service.BibParser(rules=parsing_rules, handler=marc_parser),
            updater=update_service.BibUpdater(handler=marc_updater, rules=update_rules),
        )
        matcher = match_service.BibMatcher(fetcher)
        vendor = template_data.get("vendor", "UNKNOWN")
        for file_name, data in batches.items():
            file_names.append(file_name)
            records = marc_handler.parse_and_validate_incoming(data=data, vendor=vendor)
            for bib in records:
                matches = matcher.match_order_record(bib, matchpoints=matchpoints)
                analysis = matcher.review_matches(bib=bib, matches=matches)
                bib.apply_match(bib_id=analysis.target_bib_id, action=analysis.action)
                marc_handler.apply_updates_by_record_type(
                    record=bib, record_type="sel", template_data=template_data
                )
                report_data.append(analysis.to_dict())
            processed = {"file_name": file_name, "records": marc_parser.write(records)}
            out_batches.append(processed)
        saved_batch = batch_handling.SaveProcessedFileBatch.execute(
            batch_data=out_batches,
            file_names=file_names,
            report_data=report_data,
            repo=repo,
        )
        return saved_batch
