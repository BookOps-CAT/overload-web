from overload_web.domain.pvf import commands, events


class TestWorkflowManager:
    def test_initialize_workflow(self, stub_full_level_manager, caplog):
        bus = stub_full_level_manager.bus
        bus.send(commands.InitializeWorkflow(workflow_id="12345"))
        assert "Workflow 12345 created. Status is PENDING." == caplog.records[-1].msg

    def test_start_order_level_workflow(self, stub_order_level_manager, caplog):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.StartOrderLevelRecordsWorkflow(
                collection="foo",
                library="bar",
                matchpoints={},
                record_type="baz",
                template_data={},
                vendor="UNKNOWN",
                workflow_id="12345",
            )
        )
        assert len(caplog.records) == 12
        assert "Workflow 12345 transitioned to COMPLETED" == caplog.records[-1].msg

    def test_start_full_level_workflow(self, stub_full_level_manager, caplog):
        caplog.set_level("INFO")
        bus = stub_full_level_manager.bus
        bus.send(
            commands.StartFullLevelRecordsWorkflow(
                collection="foo", library="bar", record_type="baz", workflow_id="12345"
            )
        )
        assert len(caplog.records) == 12
        assert "Workflow 12345 transitioned to COMPLETED" == caplog.records[-1].msg


class TestWorkflowManagerHandlers:
    def test_handle_workflow_initialized(self, stub_order_level_manager, caplog):
        stub_order_level_manager.handle_workflow_initialized(
            event=events.WorkflowInitialized(workflow_id="1")
        )
        assert "Workflow 1 created. Status is PENDING." in caplog.text

    def test_handle_workflow_started_order_level(
        self, stub_order_level_manager, caplog
    ):
        stub_order_level_manager.handle_workflow_started_order_level(
            event=events.OrderLevelWorkflowStarted(
                workflow_id="1",
                vendor="Foo",
                template_data={"format": "a", "vendor": "UNKNOWN"},
                matchpoints={"primary_matchpoint": "isbn"},
                library="foo",
                collection="bar",
                record_type="baz",
            )
        )
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text
        assert "Workflow 1 transitioned to MATCHING" in caplog.text
        assert "Workflow 1 transitioned to UPDATING" in caplog.text
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_started_full_level(self, stub_full_level_manager, caplog):
        stub_full_level_manager.handle_workflow_started_full_level(
            event=events.FullLevelWorkflowStarted(
                workflow_id="1", library="foo", collection="bar", record_type="baz"
            )
        )
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text
        assert "Workflow 1 transitioned to MATCHING" in caplog.text
        assert "Workflow 1 transitioned to UPDATING" in caplog.text
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text


class TestWorkflowManagerErrors:
    def test_handle_workflow_started_order_level_error(
        self, stub_order_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.StartOrderLevelRecordsWorkflow(
                workflow_id="1",
                vendor="Foo",
                template_data={"format": "a", "vendor": "UNKNOWN"},
                matchpoints={"primary_matchpoint": "isbn"},
                library="foo",
                collection="bar",
                record_type="baz",
            )
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_order_level_error(
        self, stub_order_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.ParseOrderLevelFiles(
                workflow_id="1",
                vendor="Foo",
                library="foo",
                collection="bar",
                record_type="baz",
            )
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_order_level_error(
        self, stub_order_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.MatchOrderLevelRecords(
                workflow_id="1",
                matchpoints={"primary_matchpoint": "isbn"},
                library="foo",
            )
        )

        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_order_level_error(
        self, stub_order_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.UpdateAndOutputOrderLevelRecords(
                workflow_id="1",
                template_data={"format": "a", "vendor": "UNKNOWN"},
                library="foo",
                collection="bar",
                record_type="baz",
            )
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_started_full_level_error(
        self, stub_full_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_full_level_manager.bus
        bus.send(
            commands.StartFullLevelRecordsWorkflow(
                workflow_id="1", library="foo", collection="bar", record_type="baz"
            )
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_full_level_error(
        self, stub_full_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_full_level_manager.bus
        bus.send(
            commands.ParseFullLevelFiles(
                workflow_id="1", library="foo", collection="bar", record_type="baz"
            )
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_full_level_error(
        self, stub_full_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_full_level_manager.bus
        bus.send(commands.MatchFullLevelRecords(workflow_id="1", library="foo"))
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_full_level_error(
        self, stub_full_level_manager, manager_no_workflows, caplog
    ):
        bus = stub_full_level_manager.bus
        bus.send(
            commands.UpdateAndOutputFullLevelRecords(
                workflow_id="1", library="foo", collection="bar", record_type="baz"
            )
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text
