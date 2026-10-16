import logging
from dataclasses import dataclass
from typing import Any

import pytest

from overload_web.domain.shared import Command, Event
from overload_web.infrastructure import message_bus

logger = logging.getLogger(__name__)


@dataclass
class StubCommand(Command):
    id: str


@dataclass
class StubEvent(Event):
    id: str


class TestMessageBus:
    def stub_callable(self, obj: Any) -> None:
        logger.info(f"Caller for {obj}")

    def test_message_bus(self):
        bus = message_bus.MessageBus()
        assert bus.command_handlers == {}
        assert bus.event_handlers == {}

    def test_register_command(self):
        bus = message_bus.MessageBus()
        bus.register_command(StubCommand, self.stub_callable)
        assert len(bus.command_handlers.keys()) == 1
        assert len(bus.event_handlers.keys()) == 0

    def test_register_command_overwrite(self, caplog):
        bus = message_bus.MessageBus()
        bus.register_command(StubCommand, str)
        bus.register_command(StubCommand, self.stub_callable)
        assert len(bus.command_handlers.keys()) == 1
        assert len(caplog.records) == 1
        assert caplog.records[0].msg == "Overwriting handler for StubCommand"

    def test_register_event(self):
        bus = message_bus.MessageBus()
        bus.register_event(StubEvent, self.stub_callable)
        assert len(bus.command_handlers.keys()) == 0
        assert len(bus.event_handlers.keys()) == 1

    def test_register_event_overwrite(self):
        bus = message_bus.MessageBus()
        bus.register_event(StubEvent, self.stub_callable)
        bus.register_event(StubEvent, self.stub_callable)
        assert len(bus.command_handlers.keys()) == 0
        assert len(bus.event_handlers.keys()) == 1

    def test_send(self, caplog):
        bus = message_bus.MessageBus()
        bus.register_command(StubCommand, self.stub_callable)
        bus.send(StubCommand(id="foo"))
        assert len(caplog.records) == 2
        assert caplog.records[0].msg == "Handling command: StubCommand"
        assert caplog.records[1].msg == "Caller for StubCommand(id='foo')"

    def test_send_missing_handler(self):
        bus = message_bus.MessageBus()
        with pytest.raises(ValueError) as exc:
            bus.send(StubCommand(id="foo"))
        assert str(exc.value) == "No handler registered for command StubCommand."

    def test_publish(self, caplog):
        bus = message_bus.MessageBus()
        bus.register_event(StubEvent, self.stub_callable)
        bus.publish(StubEvent(id="bar"))
        assert len(caplog.records) == 2
        assert caplog.records[0].msg == "Publishing event: StubEvent"
        assert caplog.records[1].msg == "Caller for StubEvent(id='bar')"

    def test_publish_missing_handler(self, caplog):
        bus = message_bus.MessageBus()
        bus.register_event(StubEvent, list)
        bus.publish(StubEvent(id="bar"))
        assert len(caplog.records) == 2
        assert caplog.records[0].msg == "Publishing event: StubEvent"
        assert (
            caplog.records[1].msg
            == "Error handling event StubEvent: 'StubEvent' object is not iterable"
        )
