"""Dependency injection functions."""

from __future__ import annotations

import logging

from overload_web.application.pvf import handlers, process_manager
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

    pm = process_manager.WorkflowManager(bus=bus, uow=uow)

    bus.register_command(
        commands.ParseOrderLevelFiles,
        lambda cmd: handlers.ParseOrderLevelFilesHandler.handle(
            bus=bus, cmd=cmd, storage=storage, parser=parser, uow=uow
        ),
    )
    bus.register_command(
        commands.MatchOrderLevelRecords,
        lambda cmd: handlers.MatchOrderLevelRecordsHandler.handle(
            bus=bus, cmd=cmd, matcher=matcher, storage=storage
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputOrderLevelRecords,
        lambda cmd: handlers.UpdateAndOutputOrderLevelRecordsHandler.handle(
            bus=bus, cmd=cmd, parser=parser, uow=uow, updater=updater, storage=storage
        ),
    )

    bus.register_command(
        commands.ParseFullLevelFiles,
        lambda cmd: handlers.ParseFullLevelFilesHandler.handle(
            bus=bus, cmd=cmd, storage=storage, parser=parser, uow=uow
        ),
    )
    bus.register_command(
        commands.MatchFullLevelRecords,
        lambda cmd: handlers.MatchFullLevelRecordsHandler.handle(
            bus=bus, cmd=cmd, matcher=matcher, storage=storage
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputFullLevelRecords,
        lambda cmd: handlers.UpdateAndOutputFullLevelRecordsHandler.handle(
            bus=bus, cmd=cmd, parser=parser, uow=uow, updater=updater, storage=storage
        ),
    )

    bus.register_event(events.OrderLevelFilesParsed, pm.handle_files_parsed_order_level)
    bus.register_event(
        events.OrderLevelRecordsMatched, pm.handle_records_matched_order_level
    )
    bus.register_event(
        events.OrderLevelWorkflowCompleted, pm.handle_workflow_completed_order_level
    )

    bus.register_event(events.FullLevelFilesParsed, pm.handle_files_parsed_full_level)
    bus.register_event(
        events.FullLevelRecordsMatched, pm.handle_records_matched_full_level
    )
    bus.register_event(
        events.FullLevelWorkflowCompleted, pm.handle_workflow_completed_full_level
    )

    return bus
