import logging
from dataclasses import dataclass
from typing import Any

import pytest

from overload_web.domain.pvf import events
from overload_web.domain.shared import Command, Event
from overload_web.infrastructure import message_bus, unit_of_work

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


class TestSqlModelUnitOfWork:
    def test_uow(self, mock_engine):
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        assert uow.session is None
        with uow:
            assert uow.session is not None

    def test_uow_exit_with_rollback(self, mock_engine):
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        with pytest.raises(IndexError):
            with uow:
                empty = list()
                empty[1]


class TestWorkflowManager:
    def test_handle_workflow_started_order_level(self, stub_manager, caplog):
        stub_manager.handle_workflow_started_order_level(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

    def test_handle_files_parsed_order_level(self, stub_manager, caplog):
        stub_manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_records_matched_order_level(self, stub_manager, caplog):
        stub_manager.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_handle_workflow_completed_order_level(self, stub_manager, caplog):
        stub_manager.handle_workflow_completed_order_level(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_started_full_level(self, stub_manager, caplog):
        stub_manager.handle_workflow_started_full_level(workflow_id="1")
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

    def test_handle_files_parsed_full_level(self, stub_manager, caplog):
        stub_manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_records_matched_full_level(self, stub_manager, caplog):
        stub_manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_handle_workflow_completed_full_level(self, stub_manager, caplog):
        stub_manager.handle_workflow_completed_full_level(
            event=events.FullLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text


class TestWorkflowManagerErrors:
    def test_handle_workflow_started_order_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_workflow_started_order_level(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_order_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_order_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_order_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_workflow_completed_order_level(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_started_full_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_workflow_started_full_level(workflow_id="1")
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_full_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_full_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_full_level_error(
        self, stub_manager_no_workflows, caplog
    ):
        stub_manager_no_workflows.handle_workflow_completed_full_level(
            event=events.FullLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text


class TestWorkflowManagerMockedSession:
    def test_handle_files_parsed_order_level(self, mocked_order_level_manager, caplog):
        mocked_order_level_manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_files_parsed_full_level(self, mocked_full_record_manager, caplog):
        mocked_full_record_manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_workflow_completed_order_level(
        self, mocked_order_level_manager, caplog
    ):
        mocked_order_level_manager.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_completed_full_level(
        self, mocked_full_record_manager, caplog
    ):
        mocked_full_record_manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text
