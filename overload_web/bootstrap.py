"""Dependency injection functions."""

from __future__ import annotations

import logging

from overload_web.application.pvf import handlers, workflow_manager
from overload_web.domain.pvf import commands, events, ports, services
from overload_web.infrastructure import message_bus

logger = logging.getLogger(__name__)


def bootstrap_message_bus(
    matcher: services.BibMatcher,
    parser: services.BibParser,
    uow: ports.UnitOfWorkProtocol,
    updater: services.BibUpdater,
    storage: ports.FileStorage,
) -> message_bus.MessageBus:
    bus = message_bus.MessageBus()

    pm = workflow_manager.WorkflowManager(bus=bus, uow=uow)

    bus.register_command(
        commands.InitializeWorkflow,
        handlers.InitializeWorkflowHandler(bus=bus, uow=uow),
    )
    bus.register_command(
        commands.StartOrderLevelRecordsWorkflow,
        handlers.StartOrderLevelRecordsWorkflowHandler(
            bus=bus, storage=storage, uow=uow
        ),
    )
    bus.register_command(
        commands.ParseOrderLevelFiles,
        handlers.ParseOrderLevelFilesHandler(bus=bus, storage=storage, parser=parser),
    )
    bus.register_command(
        commands.MatchOrderLevelRecords,
        handlers.MatchOrderLevelRecordsHandler(
            bus=bus, matcher=matcher, storage=storage
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputOrderLevelRecords,
        handlers.UpdateAndOutputOrderLevelRecordsHandler(
            bus=bus, uow=uow, updater=updater, storage=storage
        ),
    )
    bus.register_command(
        commands.StartFullLevelRecordsWorkflow,
        handlers.StartFullLevelRecordsWorkflowHandler(
            bus=bus, storage=storage, uow=uow
        ),
    )
    bus.register_command(
        commands.ParseFullLevelFiles,
        handlers.ParseFullLevelFilesHandler(bus=bus, storage=storage, parser=parser),
    )
    bus.register_command(
        commands.MatchFullLevelRecords,
        handlers.MatchFullLevelRecordsHandler(
            bus=bus, matcher=matcher, storage=storage
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputFullLevelRecords,
        handlers.UpdateAndOutputFullLevelRecordsHandler(
            bus=bus, uow=uow, updater=updater, storage=storage
        ),
    )
    bus.register_event(events.WorkflowInitialized, pm.handle_workflow_initialized)
    bus.register_event(
        events.OrderLevelWorkflowStarted, pm.handle_workflow_started_order_level
    )
    bus.register_event(events.OrderLevelFilesParsed, pm.handle_files_parsed_order_level)
    bus.register_event(
        events.OrderLevelRecordsMatched, pm.handle_records_matched_order_level
    )
    bus.register_event(
        events.OrderLevelWorkflowCompleted, pm.handle_workflow_completed_order_level
    )
    bus.register_event(
        events.FullLevelWorkflowStarted, pm.handle_workflow_started_full_level
    )
    bus.register_event(events.FullLevelFilesParsed, pm.handle_files_parsed_full_level)
    bus.register_event(
        events.FullLevelRecordsMatched, pm.handle_records_matched_full_level
    )
    bus.register_event(
        events.FullLevelWorkflowCompleted, pm.handle_workflow_completed_full_level
    )

    return bus
