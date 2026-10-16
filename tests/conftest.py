import datetime
import json
import random
from typing import Any

import pytest
import requests
from bookops_worldcat.errors import BookopsWorldcatError
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf import handlers
from overload_web.application.pvf.workflow_manager import WorkflowManager
from overload_web.bootstrap import bootstrap_message_bus
from overload_web.domain.pvf import aggregate, commands, models, ports, services
from overload_web.infrastructure import oclc, sierra_clients, tables, unit_of_work


@pytest.fixture(autouse=True)
def test_env(caplog, monkeypatch):
    caplog.set_level("DEBUG")
    monkeypatch.setenv("NYPL_PLATFORM_CLIENT", "foo")
    monkeypatch.setenv("NYPL_PLATFORM_SECRET", "bar")
    monkeypatch.setenv("NYPL_PLATFORM_OAUTH", "baz")
    monkeypatch.setenv("NYPL_PLATFORM_TARGET", "dev")
    monkeypatch.setenv("NYPL_PLATFORM_AGENT", "test")
    monkeypatch.setenv("BPL_SOLR_CLIENT", "foo")
    monkeypatch.setenv("BPL_SOLR_TARGET", "test")
    monkeypatch.setenv("FOO_USER", "foo")
    monkeypatch.setenv("FOO_PASSWORD", "bar")
    monkeypatch.setenv("FOO_HOST", "sftp.baz.com")
    monkeypatch.setenv("FOO_PORT", "22")
    monkeypatch.setenv("FOO_SRC", "/")
    monkeypatch.setenv("FOO_DST", "nsdrop/vendor_files/foo")
    monkeypatch.setenv("GOOGLE_SHEET_TOKEN", "foo")
    monkeypatch.setenv("GOOGLE_SHEET_REFRESH_TOKEN", "bar")
    monkeypatch.setenv("GOOGLE_SHEET_CLIENT_ID", "baz")
    monkeypatch.setenv("GOOGLE_SHEET_CLIENT_SECRET", "qux")
    monkeypatch.setenv("GOOGLE_SHEET_NAME", "sheet")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "id")
    monkeypatch.setenv("NYPL_WORLDCAT_CLIENT", "foo")
    monkeypatch.setenv("NYPL_WORLDCAT_SECRET", "bar")
    monkeypatch.setenv("BPL_WORLDCAT_CLIENT", "foo")
    monkeypatch.setenv("BPL_WORLDCAT_SECRET", "bar")


class MockHTTPResponse:
    def __init__(
        self, status_code: int, ok: bool, _json: dict, _content: bytes | None = None
    ):
        self.status_code = status_code
        self.ok = ok
        self._json = _json
        self._content = _content

    @property
    def content(self):
        return self._content

    def json(self):
        return self._json


class FakeSierraSession(sierra_clients.SierraSessionProtocol):
    def _get_credentials(self):
        return "foo"

    def _get_bibs_by_bib_id(self, value: str | int):
        pass

    def _get_bibs_by_isbn(self, value: str | int):
        pass

    def _get_bibs_by_issn(self, value: str | int):
        pass

    def _get_bibs_by_oclc_number(self, value: str | int):
        pass

    def _get_bibs_by_upc(self, value: str | int):
        pass

    def _parse_response(self, response: requests.Response) -> list[dict[str, Any]]:
        return [{"id": "123456789", "title": "foo"}]


@pytest.fixture
def mock_sierra_session(monkeypatch):
    def response(*args, **kwargs):
        record = {"id": "123456789", "title": "foo"}
        json = {"response": {"docs": [record]}, "data": [record]}
        return MockHTTPResponse(status_code=200, ok=True, _json=json)

    def token_response(*args, **kwargs):
        token_json = {"access_token": "foo", "expires_in": 10}
        return MockHTTPResponse(status_code=200, ok=True, _json=token_json)

    monkeypatch.setattr("requests.Session.get", response)
    monkeypatch.setattr("requests.post", token_response)
    return FakeSierraSession()


@pytest.fixture(scope="session")
def fake_fetcher():
    return sierra_clients.SierraBibFetcher(session=FakeSierraSession())


@pytest.fixture(scope="session")
def get_constants() -> dict[str, Any]:
    """Retrieve processing constants from JSON file."""
    with open("overload_web/data/update_rules.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    with open("overload_web/data/parsing_rules.json", "r", encoding="utf-8") as fh:
        parsing_rules = json.load(fh)
    return {"constants": constants, "parsing_rules": parsing_rules}


@pytest.fixture
def mock_wc_session(monkeypatch):
    def response(*args, **kwargs):
        json = {
            "numberOfRecords": 1,
            "briefRecords": [
                {
                    "oclcNumber": "1103229133",
                    "title": "Foo: bar",
                    "creator": "Baz",
                    "language": "eng",
                    "generalFormat": "Book",
                    "specificFormat": "PrintBook",
                    "isbns": ["9781470398842"],
                    "catalogingInfo": {
                        "catalogingAgency": "DLC",
                        "transcribingAgency": "DLC",
                        "catalogingLanguage": "eng",
                        "levelOfCataloging": " ",
                    },
                    "date": {"replaceDate": "260901"},
                }
            ],
            "date": {"replaceDate": "260901"},
        }
        return MockHTTPResponse(status_code=200, ok=True, _json=json, _content=b"")

    def token_response(*args, **kwargs):
        token_json = {
            "access_token": "foo",
            "expires_at": "2020-08-23 01:00:00Z",
            "token_type": "bearer",
        }
        return MockHTTPResponse(status_code=200, ok=True, _json=token_json)

    monkeypatch.setattr("requests.Session.send", response)
    monkeypatch.setattr("requests.post", token_response)
    return FakeOCLCSession()


@pytest.fixture
def mock_wc_session_error(monkeypatch, mock_wc_session):
    def worldcat_error(*args, **kwargs):
        raise BookopsWorldcatError

    def token_response(*args, **kwargs):
        now = datetime.datetime.now(tz=datetime.UTC)
        new_expiration = now + datetime.timedelta(hours=1)
        token_json = {
            "access_token": "foo",
            "expires_at": datetime.datetime.strftime(
                new_expiration, "%Y-%m-%d %H:%M:%SZ"
            ),
            "token_type": "bearer",
        }
        return MockHTTPResponse(status_code=200, ok=True, _json=token_json)

    monkeypatch.setattr("requests.Session.send", worldcat_error)
    monkeypatch.setattr("requests.post", token_response)
    return FakeOCLCSession()


class FakeOCLCSession:
    def _get_credentials(self):
        return "foo"

    def _check_authorization(self):
        pass

    def _parse_brief_record_response(self, response: requests.Response):
        return [
            {
                "oclcNumber": "12345678",
                "date": "2020",
                "title": "Foo.",
                "creator": "Bar",
                "language": "eng",
                "generalFormat": "Book",
                "specificFormat": "PrintBook",
                "isbns": [],
                "mergedOclcNumbers": [],
                "catalogingInfo": {
                    "catalogingAgency": "N$T",
                    "transcribingAgency": "N$T",
                    "catalogingLanguage": "eng",
                    "levelOfCataloging": "7",
                },
            }
        ]

    def _prepare_and_send_request(self, request: requests.Request):
        pass

    def _brief_bibs_get_by_id(self, params: dict[str, Any]):
        pass

    def _full_bib_get_by_id(self, value: str | int):
        return MockHTTPResponse(status_code=200, ok=True, _json={}, _content=b"")

    def _full_bib_json_get_by_id(self, oclc_number: str):
        return MockHTTPResponse(
            status_code=200, ok=True, _json={"date": {"replaceDate": "200801"}}
        )


@pytest.fixture
def fake_oclc_fetcher():
    return oclc.WorldcatFetcher(session=FakeOCLCSession())


@pytest.fixture
def fake_oclc_fetcher_no_matches(monkeypatch):
    def empty_list(*rgs, **kwargs):
        return []

    monkeypatch.setattr(oclc.WorldcatFetcher, "get_brief_bibs_by_id", empty_list)
    return oclc.WorldcatFetcher(session=FakeOCLCSession())


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
def mock_engine_with_workflow(mock_engine, mocker):
    mock_obj = mocker.Mock()
    batch = mocker.Mock(
        return_value=tables.PVFBatch(
            files=[tables.ProcessedFileModel(file_name="foo.mrc", records=b"")],
            stats=[
                {
                    "action": "insert",
                    "call_number": "Foo",
                    "call_number_match": True,
                    "duplicate_records": [],
                    "mixed": [],
                    "other": [],
                    "resource_id": "12345",
                    "target_bib_id": "23456",
                    "target_call_no": "Foo",
                    "target_title": None,
                    "updated_by_vendor": False,
                    "vendor": "UNKNOWN",
                }
            ],
            file_names=["foo.mrc"],
            total_files=1,
            total_records=1,
            missing_barcodes=[],
            processing_integrity=True,
        )
    )
    workflow = mocker.Mock(
        return_value=tables.WorkflowStateModel(id="1", status="UPDATING", batch_id=1)
    )
    mocker.patch("overload_web.infrastructure.unit_of_work.Session.get", workflow)
    mocker.patch("overload_web.infrastructure.unit_of_work.Session.flush", mock_obj)
    mocker.patch("overload_web.infrastructure.unit_of_work.Session.refresh", mock_obj)
    mocker.patch("overload_web.infrastructure.unit_of_work.Session.add", batch)
    yield mock_engine
    mock_engine.dispose()


@pytest.fixture
def mocked_order_level_manager(mock_engine_with_workflow):
    uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine_with_workflow)

    bus = bootstrap_message_bus(
        matcher=FakeMatcher(),
        parser=FakeParser(),
        updater=FakeUpdater(),
        uow=uow,
        storage=FakeFileStorageWithOrderLevelParsedFiles(),
    )

    manager = WorkflowManager(bus=bus, uow=uow)
    return manager


@pytest.fixture
def mocked_full_record_manager(mock_engine_with_workflow):
    uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine_with_workflow)

    bus = bootstrap_message_bus(
        matcher=FakeMatcher(),
        parser=FakeParser(),
        updater=FakeUpdater(),
        uow=uow,
        storage=FakeFileStorageWithFullParsedFiles(),
    )

    manager = WorkflowManager(bus=bus, uow=uow)
    return manager


def create_stub_bib(record_type: str):
    number = random.randint(0, 10000)
    barcode = f"33333{str(number).zfill(8)}"
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


class FakeUpdater(services.BibUpdater):
    def __init__(self):
        self.handler = None

    def apply_field_updates(self, record, updates):
        pass

    def get_full_record_updates(self, record):
        return []

    def get_order_level_updates(self, record, template_data):
        return []

    def write(self, records):
        return b""


class FakeBatchRepository(unit_of_work.PVFBatchRepository):
    BATCH = tables.PVFBatch(
        files=[tables.ProcessedFileModel(file_name="foo.mrc", records=b"")],
        stats=[
            {
                "action": "insert",
                "call_number": "Foo",
                "call_number_match": False,
                "duplicate_records": [],
                "mixed": [],
                "other": [],
                "resource_id": "12345",
                "target_bib_id": "23456",
                "target_call_no": "Foo",
                "target_title": None,
                "updated_by_vendor": False,
                "vendor": "UNKNOWN",
            }
        ],
        file_names=["foo.mrc"],
        total_files=1,
        total_records=1,
        missing_barcodes=[],
        processing_integrity=True,
    )

    def __init__(self):
        self.session = None

    def get(self, id):
        return self.BATCH

    def save(self, obj):
        batch = obj
        batch.id = 1
        return batch


class FakeIncomingFileRepository(unit_of_work.IncomingFileRepository):
    FILE = tables.IncomingFileModel(
        id="1",
        filename="foo.mrc",
        workflow_id="1",
        source="local",
        reference="temp/foo.mrc",
    )

    def __init__(self):
        self.session = None

    def delete(self, id):
        pass

    def list_by_id(self, id):
        files = self.FILE
        files.workflow_id = id
        return [files]

    def save(self, obj):
        return obj


class FakeTemplateRepository(unit_of_work.OrderTemplateRepository):
    TEMPLATES: list = []

    def __init__(self):
        self.session = None

    def get(self, id):
        templates = [i for i in self.TEMPLATES if i.id in [id, int(id)]]
        if templates:
            return templates[0]
        return None

    def list(self, offset, limit):
        return self.TEMPLATES

    def save(self, obj):
        if not getattr(obj, "id"):
            obj.id = self.TEMPLATES[-1].id + 1
        template = self.get(obj.id)
        if template:
            self.TEMPLATES = [i for i in self.TEMPLATES if i != template]
        self.TEMPLATES.append(obj)
        return obj

    def update(self, data, id):
        obj = self.get(id)
        if not obj:
            return None
        updates = {"id": id}
        self.TEMPLATES = [i for i in self.TEMPLATES if i != obj]
        for k, v in data.model_dump().items():
            if not getattr(obj, k):
                updates[k] = v
        new = tables.TemplateModel(**updates)
        self.TEMPLATES.append(new)
        return new


class FakeWorkflowRepository(unit_of_work.WorkflowStatusRepository):
    WORKFLOW = models.WorkflowState(id="1", status=models.WorkflowStatus.PENDING)

    def __init__(self):
        self.session = None

    def get(self, id):
        return self.WORKFLOW

    def update(self, data, id):
        for k, v in data.__dict__.items():
            if not getattr(self.WORKFLOW, k):
                setattr(self.WORKFLOW, k, v)
        return self.WORKFLOW


class FakeUnitOfWork(ports.UnitOfWorkProtocol):
    processed_batches = FakeBatchRepository()
    incoming_files = FakeIncomingFileRepository()
    order_templates = FakeTemplateRepository()
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
def stub_manager():
    uow = FakeUnitOfWork()
    updater = FakeUpdater()
    matcher = FakeMatcher()
    parser = FakeParser()
    bus = bootstrap_message_bus(
        matcher=matcher,
        parser=parser,
        uow=uow,
        updater=updater,
        storage=FakeFileStorage(),
    )
    bus.register_command(
        commands.MatchOrderLevelRecords,
        lambda cmd: handlers.MatchOrderLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            matcher=matcher,
            storage=FakeFileStorageWithOrderLevelParsedFiles(),
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputOrderLevelRecords,
        lambda cmd: handlers.UpdateAndOutputOrderLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            uow=uow,
            updater=updater,
            storage=FakeFileStorageWithOrderLevelParsedFiles(),
        ),
    )
    bus.register_command(
        commands.MatchFullLevelRecords,
        lambda cmd: handlers.MatchFullLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            matcher=matcher,
            storage=FakeFileStorageWithFullParsedFiles(),
        ),
    )
    bus.register_command(
        commands.UpdateAndOutputFullLevelRecords,
        lambda cmd: handlers.UpdateAndOutputFullLevelRecordsHandler.handle(
            bus=bus,
            cmd=cmd,
            uow=uow,
            updater=updater,
            storage=FakeFileStorageWithFullParsedFiles(),
        ),
    )
    return WorkflowManager(bus=bus, uow=uow)


@pytest.fixture
def fake_uow():
    return FakeUnitOfWork()


@pytest.fixture
def fake_uow_no_data(monkeypatch, fake_uow):
    def mock_get_data(*args, **kwargs):
        return None

    monkeypatch.setattr(FakeBatchRepository, "get", mock_get_data)
    return fake_uow


@pytest.fixture
def stub_manager_no_workflows(monkeypatch, stub_manager):
    def mock_get_workflows(*args, **kwargs):
        return None

    monkeypatch.setattr(FakeWorkflowRepository, "get", mock_get_workflows)
    return stub_manager
