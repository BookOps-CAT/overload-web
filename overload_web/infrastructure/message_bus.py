from __future__ import annotations

import logging
from typing import Callable

from overload_web.domain.pvf import ports
from overload_web.domain.shared import Command, Event

logger = logging.getLogger(__name__)


class MessageBus(ports.MessageBusPort):
    """Routes commands to specific handlers and broadcasts events to listeners."""

    def __init__(self) -> None:
        self.command_handlers: dict[type[Command], Callable] = {}
        self.event_handlers: dict[type[Event], list[Callable]] = {}

    def register_command(self, command_type: type[Command], handler: Callable) -> None:
        """Register a single handler for a specific command."""
        if command_type in self.command_handlers:
            logger.warning(f"Overwriting handler for {command_type.__name__}")
        self.command_handlers[command_type] = handler

    def register_event(self, event_type: type[Event], handler: Callable) -> None:
        """Register a listener for a specific event."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def send(self, command: Command) -> None:
        """Route a command to its exact handler."""
        logger.info(f"Handling command: {type(command).__name__}")
        handler = self.command_handlers.get(type(command))
        if not handler:
            raise Exception(
                f"No handler registered for command {type(command).__name__}"
            )

        handler(command)

    def publish(self, event: Event) -> None:
        """Broadcast an event to all registered listeners."""
        logger.info(f"Publishing event: {type(event).__name__}")
        handlers = self.event_handlers.get(type(event), [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.exception(f"Error handling event {type(event).__name__}: {e}")
