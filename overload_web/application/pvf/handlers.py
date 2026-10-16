from __future__ import annotations

import logging
from typing import Protocol

from overload_web.domain.pvf import aggregate, commands, events, ports, services

logger = logging.getLogger(__name__)


class AbstractCommandHandler(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...  # pragma: no branch


class ParseOrderLevelFilesHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        uow: ports.UnitOfWorkProtocol,
        parser: services.BibParser,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.uow = uow
        self.storage = storage
        self.parser = parser

    def __call__(self, cmd: commands.ParseOrderLevelFiles):
        job = aggregate.OrderLevelJob(workflow_id=cmd.workflow_id, vendor=cmd.vendor)

        with self.uow:
            incoming_files = self.uow.incoming_files.list_by_id(id=cmd.workflow_id)
            batches_data = {
                i.filename: self.storage.load(i.reference) for i in incoming_files
            }
            job.parse_files(batches_data=batches_data, parser=self.parser)
            self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
            self.uow.commit()
        self.bus.publish(events.OrderLevelFilesParsed(workflow_id=cmd.workflow_id))


class ParseFullLevelFilesHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        uow: ports.UnitOfWorkProtocol,
        parser: services.BibParser,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.uow = uow
        self.storage = storage
        self.parser = parser

    def __call__(self, cmd: commands.ParseFullLevelFiles):
        job = aggregate.FullRecordJob(workflow_id=cmd.workflow_id)

        with self.uow:
            incoming_files = self.uow.incoming_files.list_by_id(id=cmd.workflow_id)
            batches_data = {
                i.filename: self.storage.load(i.reference) for i in incoming_files
            }
            job.parse_files(batches_data=batches_data, parser=self.parser)
            self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
            self.uow.commit()
        self.bus.publish(events.FullLevelFilesParsed(workflow_id=cmd.workflow_id))


class MatchOrderLevelRecordsHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        matcher: services.BibMatcher,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.storage = storage
        self.matcher = matcher

    def __call__(self, cmd: commands.MatchOrderLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(matcher=self.matcher, matchpoints=cmd.matchpoints)
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.OrderLevelRecordsMatched(workflow_id=cmd.workflow_id))


class MatchFullLevelRecordsHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        matcher: services.BibMatcher,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.storage = storage
        self.matcher = matcher

    def __call__(self, cmd: commands.MatchFullLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(matcher=self.matcher)
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.FullLevelRecordsMatched(workflow_id=cmd.workflow_id))


class UpdateAndOutputOrderLevelRecordsHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        uow: ports.UnitOfWorkProtocol,
        updater: services.BibUpdater,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.uow = uow
        self.storage = storage
        self.updater = updater

    def __call__(self, cmd: commands.UpdateAndOutputOrderLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.apply_updates_and_create_batch(
            template_data=cmd.template_data, updater=self.updater
        )
        with self.uow:
            db_batch = self.uow.processed_batches.save(job.processed)
            batch_id = db_batch.id
            self.uow.commit()
        self.bus.publish(
            events.OrderLevelWorkflowCompleted(
                workflow_id=cmd.workflow_id, batch_id=batch_id
            )
        )


class UpdateAndOutputFullLevelRecordsHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        uow: ports.UnitOfWorkProtocol,
        updater: services.BibUpdater,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.uow = uow
        self.updater = updater
        self.storage = storage

    def __call__(self, cmd: commands.UpdateAndOutputFullLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.apply_updates_and_create_batch(updater=self.updater)
        with self.uow:
            db_batch = self.uow.processed_batches.save(job.processed)
            batch_id = db_batch.id
            self.uow.commit()
        self.bus.publish(
            events.FullLevelWorkflowCompleted(
                workflow_id=cmd.workflow_id, batch_id=batch_id
            )
        )
