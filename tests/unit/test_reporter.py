import pytest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.pvf.reporting import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.domain.pvf import reporting
from overload_web.infrastructure import batch_db, reporter


class MockCreds:
    def __init__(self):
        self.token = "foo"
        self.refresh_token = "bar"

    @property
    def valid(self, *args, **kwargs):
        return True

    @property
    def expired(self, *args, **kwargs):
        return False

    def refresh(self, *args, **kwargs):
        self.expired = False
        self.valid = True

    def to_json(self, *args, **kwargs):
        pass

    def run_local_server(self, *args, **kwargs):
        return self


class MockResource:
    def __init__(self):
        self.spreadsheetId = "foo"
        self.range = "bar"

    def append(self, *args, **kwargs):
        return self

    def execute(self, *args, **kwargs):
        return dict(spreadsheetId=self.spreadsheetId, tableRange=self.range)

    def spreadsheets(self, *args, **kwargs):
        return self

    def values(self, *args, **kwargs):
        return self


@pytest.fixture
def mock_config(monkeypatch) -> None:
    def mock_creds(*args, **kwargs):
        return MockCreds()

    monkeypatch.setattr(Credentials, "from_authorized_user_info", mock_creds)


@pytest.fixture
def mock_config_expired_creds(monkeypatch, mock_config):
    monkeypatch.setattr(MockCreds, "valid", False)
    monkeypatch.setattr(MockCreds, "expired", True)


@pytest.fixture
def mock_config_no_creds(monkeypatch):
    def mock_creds(*args, **kwargs):
        return MockCreds()

    def null_return(*args, **kwargs):
        return None

    monkeypatch.setattr(InstalledAppFlow, "from_client_config", mock_creds)
    monkeypatch.setattr(Credentials, "from_authorized_user_info", null_return)


@pytest.fixture
def mock_config_invalid_creds(monkeypatch, mock_config):
    def mock_error(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr(Credentials, "from_authorized_user_info", mock_error)


@pytest.fixture
def mock_sheet_service(monkeypatch) -> None:
    def mock_creds(*args, **kwargs):
        pass

    def build_sheet(*args, **kwargs):
        return MockResource()

    monkeypatch.setattr("googleapiclient.discovery.build", build_sheet)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", build_sheet)
    monkeypatch.setattr(reporter.GoogleSheetsReporter, "configure_sheet", mock_creds)


@pytest.fixture
def mock_sheet_timeout_error(monkeypatch, mock_sheet_service):
    def mock_error(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr("googleapiclient.discovery.build", mock_error)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", mock_error)


@pytest.fixture
def mock_sheet_auth_error(monkeypatch, mock_sheet_service):
    def mock_error(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr("googleapiclient.discovery.build", mock_error)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", mock_error)


@pytest.fixture
def stub_report():
    return reporting.ProcessingStatistics(
        stats=[
            {
                "action": "attach",
                "call_number": "Foo",
                "call_number_match": False,
                "duplicate_records": [],
                "mixed": [],
                "other": [],
                "resource_id": "9781234567890",
                "target_bib_id": "12345",
                "target_call_no": "Bar",
                "target_title": "Baz",
                "updated_by_vendor": False,
                "vendor": "BTSERIES",
            }
        ]
    )


@pytest.fixture(scope="class")
def test_session():
    batch1 = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="foo.mrc", records=b"")],
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
    batch2 = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="bar.mrc", records=b"")],
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
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        session.add(batch1)
        session.commit()
        session.add(batch2)
        session.commit()
        yield session
    session.close()
    test_engine.dispose()


@pytest.fixture(scope="class")
def test_session_no_records():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    session.close()
    test_engine.dispose()


@pytest.fixture(scope="class")
def test_batch_repository(test_session):
    return batch_db.PVFBatchRepository(session=test_session)


class TestReporter:
    def test_configure_sheet(self, mock_config):
        google_handler = reporter.GoogleSheetsReporter()
        creds = google_handler.configure_sheet()
        assert creds.token == "foo"
        assert creds.valid is True
        assert creds.expired is False
        assert creds.refresh_token is not None

    def test_configure_sheet_expired(self, mock_config_expired_creds):
        google_handler = reporter.GoogleSheetsReporter()
        creds = google_handler.configure_sheet()
        assert creds.token == "foo"
        assert creds.valid is True
        assert creds.expired is False
        assert creds.refresh_token is not None

    def test_configure_sheet_generate_new_creds(self, mock_config_no_creds, caplog):
        google_handler = reporter.GoogleSheetsReporter()
        creds = google_handler.configure_sheet()
        assert creds.token == "foo"
        assert creds.valid is True
        assert creds.expired is False
        assert creds.refresh_token is not None
        assert "API token not found. Running credential config flow." in caplog.text

    def test_configure_sheet_invalid_creds(self, mock_config_invalid_creds):
        google_handler = reporter.GoogleSheetsReporter()
        with pytest.raises(ValueError):
            google_handler.configure_sheet()

    def test_prep_report(self, stub_report):
        google_handler = reporter.GoogleSheetsReporter()
        prepped_report = google_handler.prep_report(
            stub_report.create_call_number_report(record_type="cat")
        )
        assert prepped_report == [
            ["BTSERIES", "9781234567890", "12345", "[]", "Foo", "Bar", "False"]
        ]

    def test_prep_report_no_data(self):
        google_handler = reporter.GoogleSheetsReporter()
        prepped_report = google_handler.prep_report([])
        assert prepped_report == []

    def test_write_report(self, mock_sheet_service, stub_report, caplog):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report.create_duplicate_report())
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    def test_write_data_to_sheet_timeout_error(
        self, mock_sheet_timeout_error, stub_report, caplog
    ):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report.create_duplicate_report())
        assert "Unable to send data to google sheet:" in caplog.text
        assert "Data not written to sheet." in caplog.text

    def test_write_data_to_sheet_auth_error(
        self, mock_sheet_auth_error, stub_report, caplog
    ):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report.create_duplicate_report())
        assert "Unable to configure google sheet API credentials:" in caplog.text
        assert "Data not written to sheet." in caplog.text


class TestProcessingStatistics:
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_call_number_report(self, stub_report, record_type):
        report = stub_report.create_call_number_report(record_type)
        assert report == [
            {
                "call_number": "Foo",
                "call_number_match": False,
                "duplicate_records": [],
                "resource_id": "9781234567890",
                "target_bib_id": "12345",
                "target_call_no": "Bar",
                "vendor": "BTSERIES",
            }
        ]

    def test_call_number_report_no_issues(self, stub_report):
        stub_report.stats[0]["call_number_match"] = True
        report = stub_report.create_call_number_report("sel")
        assert report is None

    def test_call_number_reportcat_missing_call_number(self, stub_report):
        stub_report.stats[0]["call_number"] = None
        stub_report.stats[0]["target_call_no"] = None
        stub_report.stats[0]["call_number_match"] = True
        report = stub_report.create_call_number_report("cat")
        assert report == [
            {
                "call_number": None,
                "call_number_match": True,
                "duplicate_records": [],
                "resource_id": "9781234567890",
                "target_bib_id": "12345",
                "target_call_no": None,
                "vendor": "BTSERIES",
            }
        ]

    def test_duplicate_report(self, stub_report):
        stub_report.stats[0]["duplicate_records"] = ["3456"]
        report = stub_report.create_duplicate_report()
        assert report == [
            {
                "vendor": "BTSERIES",
                "resource_id": "9781234567890",
                "target_bib_id": "12345",
                "duplicate_records": ["3456"],
                "mixed": [],
                "other": [],
            }
        ]

    def test_duplicate_report_no_dupes(self, stub_report):
        report = stub_report.create_duplicate_report()
        assert report == []

    def test_vendor_report(self, stub_report):
        report = stub_report.create_vendor_report()
        assert report == [
            {"vendor": "BTSERIES", "attach": 1, "insert": 0, "update": 0, "total": 1}
        ]


class TestReportCommands:
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_create_pvf_output_report(self, test_batch_repository, record_type):
        out = CreatePVFOutputReport.execute(
            batch_id="1", record_type=record_type, repo=test_batch_repository
        )
        assert out == {
            "total_records": 1,
            "file_names": ["foo.mrc"],
            "total_files": 1,
            "vendor_report": [
                {"vendor": "UNKNOWN", "attach": 0, "insert": 1, "update": 0, "total": 1}
            ],
            "dupes_report": [],
            "call_no_report": [
                {
                    "vendor": "UNKNOWN",
                    "resource_id": "12345",
                    "call_number": "Foo",
                    "target_bib_id": "23456",
                    "target_call_no": "Foo",
                    "call_number_match": False,
                    "duplicate_records": [],
                }
            ],
            "missing_barcodes": [],
            "processing_integrity": True,
        }

    def test_get_detailed_report_data(self, test_batch_repository):
        out = GetDetailedReportData.execute(batch_id="1", repo=test_batch_repository)
        assert sorted(out[0].keys()) == sorted(
            [
                "vendor",
                "resource_id",
                "action",
                "target_bib_id",
                "updated_by_vendor",
                "target_title",
                "call_number_match",
                "call_number",
                "target_call_no",
                "duplicate_records",
                "mixed",
                "other",
            ]
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_both_reports(
        self, mock_sheet_service, caplog, test_batch_repository, record_type
    ):
        WriteOutputReport.execute(
            batch_id="1",
            record_type=record_type,
            repo=test_batch_repository,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].message
            == "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
        )
        assert (
            caplog.records[1].message
            == "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_no_call_no_report(
        self, mock_sheet_service, caplog, test_batch_repository, record_type
    ):
        WriteOutputReport.execute(
            batch_id=2,
            record_type=record_type,
            repo=test_batch_repository,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 1
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_no_reports(
        self, mock_sheet_service, caplog, test_session_no_records, record_type
    ):
        repo = batch_db.PVFBatchRepository(session=test_session_no_records)
        WriteOutputReport.execute(
            batch_id=2,
            record_type=record_type,
            repo=repo,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 0
