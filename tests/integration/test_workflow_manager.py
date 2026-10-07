import pytest

from overload_web.application.pvf import handlers
from overload_web.application.pvf.process_manager import WorkflowManager
from overload_web.domain.pvf import (
    aggregate,
    commands,
    events,
    files,
    models,
    ports,
    services,
)
from overload_web.infrastructure import marc_handler, message_bus, tables


def create_stub_bib(record_type: str):
    return models.DomainBib(
        library="nypl",
        collection="BL",
        isbn="9781234567890",
        title="Foo",
        record_type=record_type,
        binary_data=b"",
        barcodes=["333331234567890"],
        orders=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN",
            bib_fields=[],
            matchpoints={
                "primary_matchpoint": "isbn",
                "secondary_matchpoint": "control_number",
            },
        ),
        parsed_fields=[],
    )


@pytest.fixture
def stub_updater_service():
    return services.BibUpdater(
        handler=marc_handler.MarcUpdater(),
        order_mapping={},
        default_loc="foo",
        bib_id_tag="bar",
        library="baz",
        record_type="quz",
        collection="spam",
    )


@pytest.fixture
def fake_matcher(fake_fetcher):
    return services.BibMatcher(fetcher=fake_fetcher)


class FakeFileStorage(ports.FileStorage):
    def load(*args, **kwargs):
        return b""

    def load_intermediate_records(*args, **kwargs):
        pass

    def save(*args, **kwargs):
        return "foo"

    def save_intermediate_records(*args, **kwargs):
        pass


class FakeFileStorageWithFullParsedFiles(FakeFileStorage):
    def load_intermediate_records(*args, **kwargs):
        job = aggregate.FullRecordJob(workflow_id=kwargs["id"])
        job.file_names = ["foo.mrc"]
        job.records = [create_stub_bib("cat")]
        job.report_data = [{"foo": "bar"}]
        job.records[0].action = "attach"
        return job


class FakeFileStorageWithOrderLevelParsedFiles(FakeFileStorage):
    def load_intermediate_records(*args, **kwargs):
        job = aggregate.OrderLevelJob(workflow_id=kwargs["id"], vendor="UNKNOWN")
        job.file_names = ["foo.mrc"]
        job.file_records = {"foo.mrc": [create_stub_bib("acq")]}
        job.report_data = [{"foo": "bar"}]
        return job


class FakeBatchRepository(ports.BatchRepositoryProtocol):
    def get(self, id) -> tables.PVFBatch:
        batch = tables.PVFBatch(
            id=id,
            files=[],
            stats=[],
            file_names=[],
            total_files=1,
            total_records=1,
            missing_barcodes=1,
        )
        return batch

    def save(self, obj) -> tables.PVFBatch:
        batch = obj
        batch.id = "1"
        return batch


class FakeIncomingFileRepository(ports.IncomingFileRepositoryProtocol):
    FILE = files.IncomingFile(
        id="1",
        filename="foo.mrc",
        workflow_id="1",
        source="local",
        reference="temp/foo.mrc",
    )

    def delete(self, id):
        return super().delete(id)

    def list_by_id(self, id) -> list[files.IncomingFile]:
        files = self.FILE
        files.workflow_id = id
        return [files]

    def save(self, obj):
        return super().save(obj)


class FakeWorkflowRepository(ports.WorkflowRepositoryProtocol):
    WORKFLOW = models.WorkflowState(id="1", status=models.WorkflowStatus.PENDING)

    def get(self, id) -> models.WorkflowState:
        self.WORKFLOW.id = id
        return self.WORKFLOW

    def update(self, data, id) -> None:
        self.WORKFLOW = data
        self.WORKFLOW.id = id

    def save(self, obj) -> models.WorkflowState:
        return obj


class FakeUnitOfWork(ports.UnitOfWorkProtocol):
    processed_batches = FakeBatchRepository()
    incoming_files = FakeIncomingFileRepository()
    workflow_states = FakeWorkflowRepository()

    def commit(self) -> None:
        pass


@pytest.fixture
def fake_uow_no_workflows(monkeypatch):
    def mock_get_workflows(*args, **kwargs):
        return None

    monkeypatch.setattr(FakeWorkflowRepository, "get", mock_get_workflows)
    return FakeUnitOfWork()


@pytest.fixture
def mock_parsing_service(monkeypatch):
    def mock_parse_marc_data(*args, **kwargs):
        return [create_stub_bib("acq")]

    def mock_write(*args, **kwargs):
        return b""

    monkeypatch.setattr(services.BibParser, "parse_marc_data", mock_parse_marc_data)
    monkeypatch.setattr(services.BibParser, "write", mock_write)
    return services.BibParser(
        handler=marc_handler.MarcParser(),
        library="foo",
        record_type="bar",
        collection="baz",
        vendor_mapping={},
        bib_mapping={},
        order_mapping={},
    )


@pytest.fixture
def stub_message_bus(mock_parsing_service, fake_matcher, stub_updater_service):
    bus = message_bus.MessageBus()

    pm = WorkflowManager(bus=bus, uow=FakeUnitOfWork())
    bus.register_command(
        commands.ParseOrderLevelFiles,
        lambda cmd: handlers.ParseOrderLevelFilesHandler.handle(
            bus=bus,
            cmd=cmd,
            storage=FakeFileStorage(),
            parser=mock_parsing_service,
            uow=FakeUnitOfWork(),
        ),
    )
    bus.register_command(
        commands.MatchOrderLevelRecords,
        lambda cmd: handlers.MatchOrderLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            matcher=fake_matcher,
            storage=FakeFileStorageWithOrderLevelParsedFiles(),
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputOrderLevelRecords,
        lambda cmd: handlers.UpdateAndOutputOrderLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            parser=mock_parsing_service,
            uow=FakeUnitOfWork(),
            updater=stub_updater_service,
            storage=FakeFileStorageWithOrderLevelParsedFiles(),
        ),
    )
    bus.register_command(
        commands.ParseFullLevelFiles,
        lambda cmd: handlers.ParseFullLevelFilesHandler.handle(
            bus=bus,
            cmd=cmd,
            storage=FakeFileStorage(),
            parser=mock_parsing_service,
            uow=FakeUnitOfWork(),
        ),
    )
    bus.register_command(
        commands.MatchFullLevelRecords,
        lambda cmd: handlers.MatchFullLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            matcher=fake_matcher,
            storage=FakeFileStorageWithFullParsedFiles(),
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputFullLevelRecords,
        lambda cmd: handlers.UpdateAndOutputFullLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            parser=mock_parsing_service,
            uow=FakeUnitOfWork(),
            updater=stub_updater_service,
            storage=FakeFileStorageWithFullParsedFiles(),
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


class TestWorkflowManager:
    def test_handle_workflow_started_order_level_started(
        self, stub_message_bus, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_workflow_started_order_level(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

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

    def test_handle_files_parsed_order_level(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_files_parsed_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_files_parsed_order_level(
            event=events.OrderLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_order_level(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_handle_records_matched_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_records_matched_order_level(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_order_level(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_workflow_completed_order_level(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_completed_order_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_completed_order_level(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_started_full_level_started(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_workflow_started_full_level(workflow_id="1")
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

    def test_handle_workflow_started_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_started_full_level(workflow_id="1")
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_files_parsed_full_level(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_handle_files_parsed_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_files_parsed_full_level(
            event=events.FullLevelFilesParsed(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_records_matched_full_level(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_handle_records_matched_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_records_matched_full_level(
            event=events.FullLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_handle_workflow_completed_full_level(self, stub_message_bus, caplog):
        manager = WorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_workflow_completed_full_level(
            event=events.FullLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_handle_workflow_completed_full_level_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = WorkflowManager(bus=stub_message_bus, uow=fake_uow_no_workflows)
        manager.handle_workflow_completed_full_level(
            event=events.FullLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text
