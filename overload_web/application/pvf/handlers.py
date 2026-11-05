"""Command handlers used within process vendor file application services."""

from __future__ import annotations

import logging
from typing import Protocol, TypeVar

from overload_web.domain.pvf import aggregate, commands, events, ports, services

logger = logging.getLogger(__name__)

C = TypeVar("C", bound=commands.Command, contravariant=True)


class AbstractCommandHandler(Protocol[C]):  # pragma: no branch
    """Base class for all command handlers used during vendor file processing."""

    def __call__(self, cmd: C) -> None:
        """Call a command."""
        ...


class InitializeWorkflowHandler(AbstractCommandHandler):
    """Initialize/create a new workflow."""

    def __init__(
        self, bus: ports.MessageBusPort, uow: ports.UnitOfWorkProtocol
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            uow: a `ports.UnitOfWorkProcotol` object.

        """
        self.bus = bus
        self.uow = uow

    def __call__(self, cmd: commands.InitializeWorkflow) -> None:
        """Call the `InitializeWorkflow` command.

        Args:
            cmd: a `commands.InitializeWorkflow` object containing a workflow ID

        Returns:
            None. New workflow is initialized and a `WorkflowInitialized` event
            is published to the message bus.

        """
        self.bus.publish(events.WorkflowInitialized(workflow_id=cmd.workflow_id))


class StartOrderLevelRecordsWorkflowHandler(AbstractCommandHandler):
    """Start an order-level record processing workflow."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            storage: a `ports.FileStorage` object where files will be saved.
            uow: a `ports.UnitOfWorkProcotol` object.

        """
        self.bus = bus
        self.storage = storage
        self.uow = uow

    def __call__(self, cmd: commands.StartOrderLevelRecordsWorkflow) -> None:
        """Call the `StartOrderLevelRecordsWorkflow` command.

        Args:
            cmd:
                a `commands.StartOrderLevelRecordsWorkflow` object. Command
                contains the workflow ID, library, collection, record_type,
                matchpoints, vendor, and template data for the workflow.

        Returns:
            None. New workflow is started and a `OrderLevelWorkflowStarted` event
            is published to the message bus.

        """
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
    """Start a record processing workflow for full MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        uow: ports.UnitOfWorkProtocol,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            storage: a `ports.FileStorage` object where files will be saved.
            uow: a `ports.UnitOfWorkProcotol` object.

        """
        self.bus = bus
        self.storage = storage
        self.uow = uow

    def __call__(self, cmd: commands.StartFullLevelRecordsWorkflow) -> None:
        """Call the `StartFullLevelRecordsWorkflow` command.

        Args:
            cmd:
                a `commands.StartFullLevelRecordsWorkflow` object. Command
                contains the workflow ID, library, collection, and record type
                for the workflow.

        Returns:
            None. New workflow is started and a `FullLevelWorkflowStarted` event
            is published to the message bus.

        """
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
    """Handle file parsing for files of order-level MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        parser: services.BibParser,
        storage: ports.FileStorage,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            parser: a `services.BibParser` object used to parse MARC files.
            storage: a `ports.FileStorage` object where files will be saved.

        """
        self.bus = bus
        self.parser = parser
        self.storage = storage

    def __call__(self, cmd: commands.ParseOrderLevelFiles) -> None:
        """Call the `ParseOrderLevelFiles` command.

        Args:
            cmd:
                a `commands.ParseOrderLevelFiles` object. Command
                contains the workflow ID, library, collection, record type
                and vendor for the workflow.

        Returns:
            None. Intermediate records are saved and `OrderLevelFilesParsed` event
            is published to the message bus.

        """
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
    """Handle file parsing for files of full-level MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        parser: services.BibParser,
        storage: ports.FileStorage,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            parser: a `services.BibParser` object used to parse MARC files.
            storage: a `ports.FileStorage` object where files will be saved.

        """
        self.bus = bus
        self.parser = parser
        self.storage = storage

    def __call__(self, cmd: commands.ParseFullLevelFiles) -> None:
        """Call the `ParseFullLevelFiles` command.

        Args:
            cmd:
                a `commands.ParseFullLevelFiles` object. Command
                contains the workflow ID, library, collection, and
                record type for the workflow.

        Returns:
            None. Intermediate records are saved and `FullLevelFilesParsed` event
            is published to the message bus.

        """
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.parse_files(
            parser=self.parser, library=cmd.library, record_type=cmd.record_type
        )
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.FullLevelFilesParsed(workflow_id=cmd.workflow_id))


class MatchOrderLevelRecordsHandler(AbstractCommandHandler):
    """Handle record matching for order-level MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        matcher: services.BibMatcher,
        storage: ports.FileStorage,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            matcher: a `services.BibMatcher` object used to match records in Sierra.
            storage: a `ports.FileStorage` object where files will be saved.

        """
        self.bus = bus
        self.matcher = matcher
        self.storage = storage

    def __call__(self, cmd: commands.MatchOrderLevelRecords) -> None:
        """Call the `MatchOrderLevelRecords` command.

        Args:
            cmd:
                a `commands.MatchOrderLevelRecords` object. Command contains
                the workflow ID, library, and matchpoints for the workflow.

        Returns:
            None. Intermediate records are saved and `OrderLevelRecordsMatched` event
            is published to the message bus.

        """
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(
            matcher=self.matcher, matchpoints=cmd.matchpoints, library=cmd.library
        )
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.OrderLevelRecordsMatched(workflow_id=cmd.workflow_id))


class MatchFullLevelRecordsHandler(AbstractCommandHandler):
    """Handle record matching for full-level MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        matcher: services.BibMatcher,
        storage: ports.FileStorage,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            matcher: a `services.BibMatcher` object used to match records in Sierra.
            storage: a `ports.FileStorage` object where files will be saved.

        """
        self.bus = bus
        self.matcher = matcher
        self.storage = storage

    def __call__(self, cmd: commands.MatchFullLevelRecords) -> None:
        """Call the `MatchFullLevelRecords` command.

        Args:
            cmd:
                a `commands.MatchFullLevelRecords` object. Command contains
                the workflow ID, and library, for the workflow.

        Returns:
            None. Intermediate records are saved and `FullLevelRecordsMatched`
            event is published to the message bus.

        """
        job = self.storage.load_intermediate_records(id=cmd.workflow_id)
        job.match_records(matcher=self.matcher, library=cmd.library)
        self.storage.save_intermediate_records(id=cmd.workflow_id, job=job)
        self.bus.publish(events.FullLevelRecordsMatched(workflow_id=cmd.workflow_id))


class UpdateAndOutputOrderLevelRecordsHandler(AbstractCommandHandler):
    """Handle record updates and file outputs for order-level MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            storage: a `ports.FileStorage` object where files will be saved.
            updater: a `services.BibUpdater` object used to update MARC records.
            uow: a `ports.UnitOfWorkProcotol` object.

        """
        self.bus = bus
        self.storage = storage
        self.uow = uow
        self.updater = updater

    def __call__(self, cmd: commands.UpdateAndOutputOrderLevelRecords) -> None:
        """Call the `UpdateAndOutputOrderLevelRecords` command.

        Args:
            cmd:
                a `commands.UpdateAndOutputOrderLevelRecords` object.
                Command contains the workflow ID, library, collection,
                record type, and template data for the workflow.

        Returns:
            None. Workflow is completed and a  `OrderLevelWorkflowCompleted`
            event is published to the message bus.

        """
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
    """Handle record updates and file outputs for full-level MARC records."""

    def __init__(
        self,
        bus: ports.MessageBusPort,
        storage: ports.FileStorage,
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
    ) -> None:
        """Initialize the handler with injected dependencies and application services.

        Args:
            bus: a `ports.MessageBusPort` object.
            storage: a `ports.FileStorage` object where files will be saved.
            updater: a `services.BibUpdater` object used to update MARC records.
            uow: a `ports.UnitOfWorkProcotol` object.


        """
        self.bus = bus
        self.storage = storage
        self.uow = uow
        self.updater = updater

    def __call__(self, cmd: commands.UpdateAndOutputFullLevelRecords) -> None:
        """Call the `UpdateAndOutputFullLevelRecords` command.

        Args:
            cmd:
                a `commands.UpdateAndOutputFullLevelRecords` object.
                Command contains the workflow ID, library, collection,
                and record type for the workflow.

        Returns:
            None. Workflow is completed and a `FullLevelWorkflowCompleted`
            event is published to the message bus.

        """
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
