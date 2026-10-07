import pytest

from overload_web.application.pvf.process_manager import WorkflowManager
from overload_web.domain.pvf import commands, events
from overload_web.infrastructure import message_bus


class TestWorkflowManager:
    def test_handle_workflow_started_order_level(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_workflow_started_order_level(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

    def test_handle_files_parsed_order_level(self, stub_message_bus, fake_uow, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_records_matched_order_level(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_handle_workflow_completed_order_level(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_workflow_completed_order_level(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_started_full_level(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_workflow_started_full_level(workflow_id="1")
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

    def test_handle_files_parsed_full_level(self, stub_message_bus, fake_uow, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_records_matched_full_level(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_handle_workflow_completed_full_level(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        manager.handle_workflow_completed_full_level(
            event=events.FullLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text


class TestWorkflowManagerMockedSession:
    def test_handle_files_parsed_order_level_error(
        self, stub_message_bus, mocked_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=mocked_uow_no_workflows)
        manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_full_level_error(
        self, stub_message_bus, mocked_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=mocked_uow_no_workflows)
        manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_order_level(
        self, stub_message_bus, mocked_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=mocked_uow)
        manager.handle_records_matched_full_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_completed_full_level(
        self, stub_message_bus, mocked_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=mocked_uow)
        manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text


class TestWorkflowManagerErrors:
    def test_handle_workflow_started_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_started_order_level(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_completed_order_level(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_started_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_started_full_level(workflow_id="1")
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_completed_full_level(
            event=events.FullLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_message_bus_missing_command_handler_error(self, fake_uow):
        manager = WorkflowManager(bus=message_bus.MessageBus(), uow=fake_uow)
        with pytest.raises(ValueError) as exc:
            manager.handle_workflow_started_order_level(
                workflow_id="1",
                vendor="Foo",
                template_data={"format": "a", "vendor": "UNKNOWN"},
                matchpoints={"primary_matchpoint": "isbn"},
            )
        assert (
            str(exc.value) == "No handler registered for command ParseOrderLevelFiles."
        )

    def test_message_bus_missing_command_handler_logs(
        self, stub_message_bus, fake_uow, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow)
        del stub_message_bus.command_handlers[commands.MatchOrderLevelRecords]
        manager.handle_workflow_started_order_level(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert (
            caplog.records[-1].msg
            == "Error handling event OrderLevelFilesParsed: No handler registered for command MatchOrderLevelRecords."
        )
