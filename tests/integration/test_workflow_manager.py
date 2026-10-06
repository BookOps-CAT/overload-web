import pytest

from overload_web.application.pvf import handlers
from overload_web.application.pvf.process_manager import OrderLevelWorkflowManager
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


def create_stub_bib():
    return models.DomainBib(
        library="nypl",
        collection="BL",
        isbn="9781234567890",
        title="Foo",
        record_type="acq",
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
def stub_order_level_job():
    job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
    job.file_names = ["foo.mrc"]
    job.file_records = {"foo.mrc": [create_stub_bib()]}
    return job


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


class FakeFileStorageWithParsedFiles(FakeFileStorage):
    def load_intermediate_records(*args, **kwargs):
        job = aggregate.OrderLevelJob(workflow_id=kwargs["id"], vendor="UNKNOWN")
        job.file_names = ["foo.mrc"]
        job.file_records = {"foo.mrc": [create_stub_bib()]}
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
        return [create_stub_bib()]

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

    pm = OrderLevelWorkflowManager(bus=bus, uow=FakeUnitOfWork())
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
            storage=FakeFileStorageWithParsedFiles(),
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
            storage=FakeFileStorageWithParsedFiles(),
        ),
    )
    bus.register_event(events.OrderLevelFilesParsed, pm.handle_files_parsed)
    bus.register_event(events.OrderLevelRecordsMatched, pm.handle_records_matched)
    bus.register_event(events.OrderLevelWorkflowCompleted, pm.handle_workflow_completed)
    return bus


class TestOrderLevelJob:
    def test_order_level_job(self):
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        assert job.file_names == []
        assert job.file_records == {}
        assert job.missing_barcodes == []
        assert job.processed_files == []
        assert job.report_data == []
        assert hasattr(job.validator, "validate_unique")

    def test_order_level_job_parse_files(self, mock_parsing_service):
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        job.parse_files(batches_data={"foo.mrc": b""}, parser=mock_parsing_service)
        assert job.file_names == ["foo.mrc"]
        assert job.file_records["foo.mrc"][0].isbn == "9781234567890"
        assert job.missing_barcodes == []
        assert job.processed_files == []
        assert job.report_data == []

    def test_order_level_job_match_records(self, fake_matcher, stub_order_level_job):
        stub_order_level_job.match_records(
            matcher=fake_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert stub_order_level_job.missing_barcodes == []
        assert stub_order_level_job.processed_files == []
        assert len(stub_order_level_job.report_data) == 1
        assert stub_order_level_job.report_data[0]["resource_id"] == "9781234567890"

    def test_order_level_job_apply_updates_and_create_batch(
        self, mock_parsing_service, stub_order_level_job, stub_updater_service
    ):
        processed_batch = stub_order_level_job.apply_updates_and_create_batch(
            parser=mock_parsing_service,
            template_data={"format": "a"},
            updater=stub_updater_service,
        )
        assert stub_order_level_job.missing_barcodes == []
        assert len(stub_order_level_job.processed_files) == 1
        assert processed_batch.files == stub_order_level_job.processed_files


class TestOrderLevelWorkflowManager:
    def test_order_level_handle_workflow_started(self, stub_message_bus, caplog):
        manager = OrderLevelWorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_workflow_started(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Workflow 1 transitioned to PROCESSING" in caplog.text

    def test_order_level_handle_workflow_started_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = OrderLevelWorkflowManager(
            bus=stub_message_bus, uow=fake_uow_no_workflows
        )
        manager.handle_workflow_started(
            workflow_id="1",
            vendor="Foo",
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_order_level_handle_files_parsed(self, stub_message_bus, caplog):
        manager = OrderLevelWorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_files_parsed(event=events.OrderLevelFilesParsed(workflow_id="1"))
        assert "Workflow 1 transitioned to MATCHING" in caplog.text

    def test_order_level_handle_files_parsed_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = OrderLevelWorkflowManager(
            bus=stub_message_bus, uow=fake_uow_no_workflows
        )
        manager.handle_files_parsed(event=events.OrderLevelFilesParsed(workflow_id="1"))
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_order_level_handle_records_matched(self, stub_message_bus, caplog):
        manager = OrderLevelWorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_records_matched(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Workflow 1 transitioned to UPDATING" in caplog.text

    def test_order_level_handle_records_matched_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = OrderLevelWorkflowManager(
            bus=stub_message_bus, uow=fake_uow_no_workflows
        )
        manager.handle_records_matched(
            event=events.OrderLevelRecordsMatched(workflow_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text

    def test_order_level_handle_workflow_completed(self, stub_message_bus, caplog):
        manager = OrderLevelWorkflowManager(bus=stub_message_bus, uow=FakeUnitOfWork())
        manager.handle_workflow_completed(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Workflow 1 transitioned to COMPLETED" in caplog.text

    def test_order_level_handle_workflow_completed_error(
        self, stub_message_bus, fake_uow_no_workflows, caplog
    ):
        manager = OrderLevelWorkflowManager(
            bus=stub_message_bus, uow=fake_uow_no_workflows
        )
        manager.handle_workflow_completed(
            event=events.OrderLevelWorkflowCompleted(workflow_id="1", batch_id="1")
        )
        assert "Cannot update state: Workflow 1 not found." in caplog.text
