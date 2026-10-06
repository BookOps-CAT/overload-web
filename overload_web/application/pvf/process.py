"""Application serivce commands for the process vendor file service."""

import logging
from typing import Any

from overload_web.domain.pvf import aggregate, ports, services

logger = logging.getLogger(__name__)


class ProcessOrderLevelRecords:
    """Parses, matches, and analyzes order-level MARC records for acquisitions."""

    @staticmethod
    def execute(
        matcher: services.BibMatcher,
        matchpoints: dict[str, str],
        parser: services.BibParser,
        storage: ports.FileStorage,
        template_data: dict[str, Any],
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
    ) -> int:
        """
        Process order-level MARC records.

        This service parses order-level MARC records, matches them against Sierra,
        analyzes all bibs that were returned as matches, updates the records with
        required fields, and outputs the updated records and the match analysis.

        Args:
            matcher:
                a `services.BibMatcher` object used by the command.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            parser:
                a `parsing_service.BibParser` object used by the command.
            storage:
                a `ports.FileStorage` object used by the command.
            template_data:
                order template data as a dictionary.
            updater:
                a `services.BibUpdater` object used by the command.
            uow:
                a `ports.UnitOfWorkProtocol` object used by the command.
            workflow_id:
                the ID associated with this processing workflow.

        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
        """
        job = aggregate.OrderLevelJob(
            workflow_id=workflow_id, vendor=template_data.get("vendor", "UNKNOWN")
        )
        with uow:
            incoming_files = uow.incoming_files.list_by_id(workflow_id)
            batches_data = {
                i.filename: storage.load(i.reference) for i in incoming_files
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
            batch_id = db_batch.id
            uow.commit()
        logger.info(f"Finished processing batch {batch_id}")
        return batch_id


class ProcessFullRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        matcher: services.BibMatcher,
        parser: services.BibParser,
        storage: ports.FileStorage,
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
    ) -> int:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the match analysis.

        Args:
            matcher:
                a `services.BibMatcher` object used by the command.
            parser:
                a `parsing_service.BibParser` object used by the command.
            storage:
                a `ports.FileStorage` object used by the command.
            updater:
                a `services.BibUpdater` object used by the command.
            uow:
                a `ports.UnitOfWorkProtocol` object used by the command.
            workflow_id:
                the ID associated with this processing workflow.

        Returns:
            A dictionary representing the processed files that were saved as a
            `ProcessedFileBatch` object in the db.
        """
        job = aggregate.FullRecordJob(workflow_id=workflow_id)
        with uow:
            incoming_files = uow.incoming_files.list_by_id(workflow_id)
            batches_data = {
                i.filename: storage.load(i.reference) for i in incoming_files
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
            batch_id = db_batch.id
            uow.commit()

        return batch_id
