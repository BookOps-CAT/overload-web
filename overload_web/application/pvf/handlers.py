from __future__ import annotations

import logging

from overload_web.domain.pvf import aggregate, commands, events, ports, services

logger = logging.getLogger(__name__)


class ParseOrderLevelFilesHandler:
    @staticmethod
    def handle(
        bus: ports.MessageBusPort,
        cmd: commands.ParseOrderLevelFiles,
        parser: services.BibParser,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
    ):
        job = aggregate.OrderLevelJob(workflow_id=cmd.workflow_id, vendor=cmd.vendor)

        with uow:
            incoming_files = uow.incoming_files.list_by_id(id=cmd.workflow_id)
            batches_data = {
                i.filename: storage.load(i.reference) for i in incoming_files
            }
            job.parse_files(batches_data=batches_data, parser=parser)
            storage.save_intermediate_records(id=cmd.workflow_id, job=job)
            uow.commit()
        bus.publish(events.OrderLevelFilesParsed(workflow_id=cmd.workflow_id))


class MatchOrderLevelRecordsHandler:
    @staticmethod
    def handle(
        bus: ports.MessageBusPort,
        cmd: commands.MatchOrderLevelRecords,
        matcher: services.BibMatcher,
        storage: ports.FileStorage,
    ):
        job = storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(matcher=matcher, matchpoints=cmd.matchpoints)
        storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        bus.publish(events.OrderLevelRecordsMatched(workflow_id=cmd.workflow_id))


class UpdateAndOutputOrderLevelRecordsHandler:
    @staticmethod
    def handle(
        bus: ports.MessageBusPort,
        cmd: commands.UpdateAndOutputOrderLevelRecords,
        parser: services.BibParser,
        uow: ports.UnitOfWorkProtocol,
        updater: services.BibUpdater,
        storage: ports.FileStorage,
    ):
        job = storage.load_intermediate_records(id=cmd.workflow_id)
        processed_batch = job.apply_updates_and_create_batch(
            parser=parser, template_data=cmd.template_data, updater=updater
        )
        with uow:
            db_batch = uow.processed_batches.save(processed_batch)
            batch_id = db_batch.id
            uow.commit()
        bus.publish(
            events.OrderLevelWorkflowCompleted(
                workflow_id=cmd.workflow_id, batch_id=batch_id
            )
        )
