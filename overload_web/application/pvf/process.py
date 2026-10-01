"""Application serivce commands for the process vendor file service."""

import logging
from typing import Any

from overload_web.domain.pvf import (
    aggregate,
    match_service,
    parsing_service,
    ports,
    update_service,
)

logger = logging.getLogger(__name__)


class ProcessAcquisitionsRecords:
    """Parses, matches, and analyzes order-level MARC records for acquisitions."""

    @staticmethod
    def execute(
        matcher: match_service.BibMatcher,
        matchpoints: dict[str, str],
        parser: parsing_service.BibParser,
        storage: ports.FileStorage,
        template_data: dict[str, Any],
        updater: update_service.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
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
        job = aggregate.AcquisitionJob(
            workflow_id=workflow_id, vendor=template_data.get("vendor", "UNKNOWN")
        )
        with uow:
            incoming_files = uow.incoming_files.list_by_id(workflow_id)
            batches_data = {
                i["filename"]: storage.load(i["reference"]) for i in incoming_files
            }

            logger.info(
                f"Loading all files for workflow {workflow_id}: {batches_data}."
            )
            job.process(
                batches_data=batches_data,
                parser=parser,
                matcher=matcher,
                updater=updater,
                matchpoints=matchpoints,
                template_data=template_data,
            )
            processed_batch = job.create_batch()
            db_batch = uow.processed_batches.save(processed_batch)
            uow.commit()

        return db_batch


class ProcessCatalogingRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        matcher: match_service.BibMatcher,
        parser: parsing_service.BibParser,
        updater: update_service.BibUpdater,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
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
        job = aggregate.CatalogingJob(workflow_id=workflow_id)
        with uow:
            incoming_files = uow.incoming_files.list_by_id(workflow_id)
            batches_data = {
                i["filename"]: storage.load(i["reference"]) for i in incoming_files
            }

            logger.info(
                f"Loading all files for workflow {workflow_id}: {batches_data}."
            )
            job.process(
                batches_data=batches_data,
                parser=parser,
                matcher=matcher,
                updater=updater,
            )
            processed_batch = job.create_batch()
            db_batch = uow.processed_batches.save(processed_batch)
            uow.commit()

        return db_batch


class ProcessSelectionRecords:
    """Parses, matches, and analyzes order-level MARC records for selection."""

    @staticmethod
    def execute(
        matcher: match_service.BibMatcher,
        matchpoints: dict[str, str],
        parser: parsing_service.BibParser,
        storage: ports.FileStorage,
        template_data: dict[str, Any],
        updater: update_service.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
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
        job = aggregate.SelectionJob(
            workflow_id=workflow_id, vendor=template_data.get("vendor", "UNKNOWN")
        )
        with uow:
            incoming_files = uow.incoming_files.list_by_id(workflow_id)
            batches_data = {
                i["filename"]: storage.load(i["reference"]) for i in incoming_files
            }

            logger.info(
                f"Loading all files for workflow {workflow_id}: {batches_data}."
            )
            job.process(
                batches_data=batches_data,
                parser=parser,
                matcher=matcher,
                updater=updater,
                matchpoints=matchpoints,
                template_data=template_data,
            )
            processed_batch = job.create_batch()
            db_batch = uow.processed_batches.save(processed_batch)
            uow.commit()

        return db_batch
