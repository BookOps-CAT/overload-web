import pytest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

from overload_web.domain.pvf import reporting
from overload_web.infrastructure import reporter


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
