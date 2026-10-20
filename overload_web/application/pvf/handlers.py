from __future__ import annotations

import logging
from typing import Protocol

from overload_web.domain.pvf import aggregate, commands, events, ports, services

logger = logging.getLogger(__name__)


class AbstractCommandHandler(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...  # pragma: no branch


class InitializeWorkflowHandler(AbstractCommandHandler):
    def __init__(self, bus: ports.MessageBusPort, uow: ports.UnitOfWorkProtocol):
        self.bus = bus
        self.uow = uow

    def __call__(self, cmd: commands.InitializeWorkflow):
        self.bus.publish(events.WorkflowInitialized(workflow_id=cmd.workflow_id))


class StartOrderLevelRecordsWorkflowHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
    ):
        self.bus = bus
        self.storage = storage
        self.uow = uow

    def __call__(self, cmd: commands.StartOrderLevelRecordsWorkflow):
        job = aggregate.OrderLevelJob(workflow_id=cmd.workflow_id, vendor=cmd.vendor)
        with self.uow:
            incoming_files = self.uow.incoming_files.list_by_id(id=cmd.workflow_id)
            job.load_files(files=incoming_files, storage=self.storage)
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(
            events.OrderLevelWorkflowStarted(
                workflow_id=cmd.workflow_id,
                vendor=cmd.vendor,
                matchpoints=cmd.matchpoints,
                template_data=cmd.template_data,
                library=cmd.library,
                collection=cmd.collection,
                record_type=cmd.record_type,
            )
        )


class StartFullLevelRecordsWorkflowHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
    ):
        self.bus = bus
        self.storage = storage
        self.uow = uow

    def __call__(self, cmd: commands.StartFullLevelRecordsWorkflow):
        job = aggregate.FullRecordJob(workflow_id=cmd.workflow_id)
        with self.uow:
            incoming_files = self.uow.incoming_files.list_by_id(id=cmd.workflow_id)
            job.load_files(files=incoming_files, storage=self.storage)
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(
            events.FullLevelWorkflowStarted(
                workflow_id=cmd.workflow_id,
                library=cmd.library,
                collection=cmd.collection,
                record_type=cmd.record_type,
            )
        )


class ParseOrderLevelFilesHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        parser: services.BibParser,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.parser = parser
        self.storage = storage

    def __call__(self, cmd: commands.ParseOrderLevelFiles):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.parse_files(
            parser=self.parser,
            library=cmd.library,
            record_type=cmd.record_type,
            vendor=cmd.vendor,
        )
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.OrderLevelFilesParsed(workflow_id=cmd.workflow_id))


class ParseFullLevelFilesHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        parser: services.BibParser,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.parser = parser
        self.storage = storage

    def __call__(self, cmd: commands.ParseFullLevelFiles):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.parse_files(
            parser=self.parser, library=cmd.library, record_type=cmd.record_type
        )
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.FullLevelFilesParsed(workflow_id=cmd.workflow_id))


class MatchOrderLevelRecordsHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        matcher: services.BibMatcher,
        storage: ports.FileStorage,
    ):
        self.bus = bus
        self.matcher = matcher
        self.storage = storage

    def __call__(self, cmd: commands.MatchOrderLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(
            matcher=self.matcher, matchpoints=cmd.matchpoints, library=cmd.library
        )
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
        self.matcher = matcher
        self.storage = storage

    def __call__(self, cmd: commands.MatchFullLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(matcher=self.matcher, library=cmd.library)
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.FullLevelRecordsMatched(workflow_id=cmd.workflow_id))


class UpdateAndOutputOrderLevelRecordsHandler(AbstractCommandHandler):
    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
    ):
        self.bus = bus
        self.storage = storage
        self.uow = uow
        self.updater = updater

    def __call__(self, cmd: commands.UpdateAndOutputOrderLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.apply_updates_and_create_batch(
            collection=cmd.collection,
            library=cmd.library,
            template_data=cmd.template_data,
            updater=self.updater,
            record_type=cmd.record_type,
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
        storage: ports.FileStorage,
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
    ):
        self.bus = bus
        self.storage = storage
        self.uow = uow
        self.updater = updater

    def __call__(self, cmd: commands.UpdateAndOutputFullLevelRecords):
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.apply_updates_and_create_batch(
            updater=self.updater, collection=cmd.collection, library=cmd.library
        )
        with self.uow:
            db_batch = self.uow.processed_batches.save(job.processed)
            batch_id = db_batch.id
            self.uow.commit()
        self.bus.publish(
            events.FullLevelWorkflowCompleted(
                workflow_id=cmd.workflow_id, batch_id=batch_id
            )
        )
