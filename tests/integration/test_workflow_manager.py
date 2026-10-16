from overload_web.domain.pvf import events


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
