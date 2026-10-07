from __future__ import annotations

import random

import pytest
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf import handlers
from overload_web.bootstrap import bootstrap_message_bus
from overload_web.domain.pvf import aggregate, commands, files, models, ports, services
from overload_web.infrastructure import tables, unit_of_work


class FakeFileRetriever:
    def __init__(self) -> None:
        pass

    def list(self, dir: str) -> list[str]:
        return ["foo.mrc"]

    def download(self, name: str, dir: str) -> bytes:
        return b""


@pytest.fixture
def mock_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def mock_engine_with_workflow(monkeypatch, mock_engine):
    def mock_get(*args, **kwargs):
        return tables.WorkflowState(id="1", status="UPDATING", batch_id=1)

    def null_return(*args, **kwargs):
        pass

    monkeypatch.setattr("sqlmodel.Session.get", mock_get)
    monkeypatch.setattr("sqlmodel.Session.flush", null_return)
    monkeypatch.setattr("sqlmodel.Session.add", null_return)
    monkeypatch.setattr("sqlmodel.Session.refresh", null_return)
    yield mock_engine
    mock_engine.dispose()


@pytest.fixture
def mocked_uow(
    mock_engine_with_workflow, monkeypatch, fake_matcher, fake_parser, fake_updater
):
    uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine_with_workflow)

    def bootstrap_bus(*args, **kwargs):
        return bootstrap_message_bus(fake_matcher, fake_parser, fake_updater, uow)

    monkeypatch.setattr("overload_web.bootstrap.bootstrap_message_bus", bootstrap_bus)
    return uow


@pytest.fixture
def mocked_uow_no_workflows(monkeypatch, mock_engine):
    def null_return(*args, **kwargs):
        pass

    monkeypatch.setattr("sqlmodel.Session.get", null_return)
    return unit_of_work.SqlModelUnitOfWork(engine=mock_engine)


def create_stub_bib(record_type: str):
    number = random.randint(0, 100)
    barcode = f"33333{str(number).zfill(10)}"
    return models.DomainBib(
        library="nypl",
        collection="BL",
        isbn="9781234567890",
        title="Foo",
        record_type=record_type,
        binary_data=b"",
        barcodes=[barcode],
        orders=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN", bib_fields=[], matchpoints={"primary_matchpoint": "isbn"}
        ),
        parsed_fields=[],
    )


class FakeMatcher(services.BibMatcher):
    RESPONSE = {
        "call_number": "Foo",
        "id": "12345",
        "isbn": ["9781234567890"],
        "sm_bib_varfields": ["005 || 20200101000001.0", "024 || {{a}} 12345"],
        "sm_item_data": ['{"barcode": "33333123456789"}'],
        "ss_marc_tag_001": "ocn123456789",
        "ss_marc_tag_003": "OCoLC",
        "ss_marc_tag_005": "20000101010000.0",
        "title": "Record 1",
    }

    def __init__(self):
        self.fetcher = None

    def match_order_record(self, record, matchpoints):
        return [self.RESPONSE]

    def match_full_record(self, record):
        return [self.RESPONSE]


class FakeParser(services.BibParser):
    def __init__(self):
        self.count = 1

    def combine_marc_files(self, data):
        self.count = len(data)
        return b""

    def parse_marc_data(self, data, vendor="UNKNOWN"):
        return [create_stub_bib("cat") for _ in [None] * self.count]

    def write(self, records):
        return b""


class FakeUpdater(services.BibUpdater):
    def __init__(self):
        self.handler = None

    def apply_field_updates(self, record, updates):
        pass

    def get_full_record_updates(self, record):
        return []

    def get_order_level_updates(self, record, template_data):
        return []


class FakeBatchRepository(unit_of_work.PVFBatchRepository):
    def __init__(self):
        self.session = None

    def save(self, obj):
        batch = obj
        batch.id = 1
        return batch


class FakeIncomingFileRepository(unit_of_work.IncomingFileRepository):
    FILE = files.IncomingFile(
        id="1",
        filename="foo.mrc",
        workflow_id="1",
        source="local",
        reference="temp/foo.mrc",
    )

    def __init__(self):
        self.session = None

    def list_by_id(self, id):
        files = self.FILE
        files.workflow_id = id
        return [files]


class FakeWorkflowRepository(unit_of_work.WorkflowStatusRepository):
    WORKFLOW = models.WorkflowState(id="1", status=models.WorkflowStatus.PENDING)

    def __init__(self):
        self.session = None

    def get(self, id):
        self.WORKFLOW.id = id
        return self.WORKFLOW

    def update(self, data, id):
        self.WORKFLOW = data
        self.WORKFLOW.id = id


class FakeUnitOfWork(ports.UnitOfWorkProtocol):
    processed_batches = FakeBatchRepository()
    incoming_files = FakeIncomingFileRepository()
    workflow_states = FakeWorkflowRepository()

    def commit(self) -> None:
        pass


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


@pytest.fixture
def fake_matcher():
    return FakeMatcher()


@pytest.fixture
def fake_parser():
    return FakeParser()


@pytest.fixture
def fake_updater():
    return FakeUpdater()


@pytest.fixture
def fake_uow():
    return FakeUnitOfWork()


@pytest.fixture
def fake_uow_no_workflows(monkeypatch):
    def mock_get_workflows(*args, **kwargs):
        return None

    monkeypatch.setattr(FakeWorkflowRepository, "get", mock_get_workflows)
    return FakeUnitOfWork()


@pytest.fixture
def stub_message_bus(fake_matcher, fake_parser, fake_updater, fake_uow):
    bus = bootstrap_message_bus(
        matcher=fake_matcher,
        parser=fake_parser,
        uow=fake_uow,
        updater=fake_updater,
        storage=FakeFileStorage(),
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
            parser=fake_parser,
            uow=fake_uow,
            updater=fake_updater,
            storage=FakeFileStorageWithOrderLevelParsedFiles(),
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
            parser=fake_parser,
            uow=fake_uow,
            updater=fake_updater,
            storage=FakeFileStorageWithFullParsedFiles(),
        ),
    )
    return bus
