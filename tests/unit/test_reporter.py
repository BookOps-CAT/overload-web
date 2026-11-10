"""Test reporting via infrastructure layer reporter and application services."""

import pytest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

from overload_web.application.pvf.report_service import WriteOutputReport
from overload_web.infrastructure import reporter


class MockCreds:
    def __init__(self) -> None:
        self.token = "foo"
        self.refresh_token = "bar"

    @property
    def valid(self):
        return True

    @property
    def expired(self):
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
def mock_sheet_timeout_error(monkeypatch, mock_config):

    def mock_error(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr("googleapiclient.discovery.build", mock_error)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", mock_error)


@pytest.fixture
def mock_sheet_service(mocker) -> None:
    mock = mocker.Mock()
    mocker.patch("googleapiclient.discovery.build", mock)
    mocker.patch("googleapiclient.discovery.build_from_document", mock)
    mocker.patch.object(reporter.GoogleSheetsReporter, "configure_sheet", mock)


class TestReporter:
    REPORT_HANDLER = reporter.GoogleSheetsReporter()

    def test_configure_sheet(self, mock_config):
        creds = self.REPORT_HANDLER.configure_sheet()
        assert creds.token == "foo"
        assert creds.valid is True
        assert creds.expired is False
        assert creds.refresh_token is not None

    def test_configure_sheet_expired(self, mock_config_expired_creds):
        creds = self.REPORT_HANDLER.configure_sheet()
        assert creds.token == "foo"
        assert creds.valid is True
        assert creds.expired is False
        assert creds.refresh_token is not None

    def test_configure_sheet_generate_new_creds(self, mock_config_no_creds, caplog):
        creds = self.REPORT_HANDLER.configure_sheet()
        assert creds.token == "foo"
        assert creds.valid is True
        assert creds.expired is False
        assert creds.refresh_token is not None
        assert "API token not found. Running credential config flow." in caplog.text

    def test_configure_sheet_invalid_creds(self, mock_config_invalid_creds, caplog):
        with pytest.raises(ValueError):
            self.REPORT_HANDLER.configure_sheet()
        assert "Unable to configure google sheet API credentials." in caplog.text

    def test_prep_report(self):
        prepped_report = self.REPORT_HANDLER.prep_report(
            [
                {
                    "vendor": "BTSERIES",
                    "resource_id": "9781234567890",
                    "target_bib_id": "12345",
                    "duplicate_records": [],
                    "call_number": "Foo",
                    "target_call_no": "Bar",
                    "call_number_match": False,
                }
            ]
        )
        assert prepped_report == [
            ["BTSERIES", "9781234567890", "12345", "[]", "Foo", "Bar", "False"]
        ]

    def test_prep_report_no_data(self):
        prepped_report = self.REPORT_HANDLER.prep_report([])
        assert prepped_report == []

    def test_write_data_to_sheet_timeout_error(self, mock_sheet_timeout_error, caplog):
        self.REPORT_HANDLER.write_report(
            [["BTSERIES", "9781234567890", "12345", "[]", "Foo", "Bar", "False"]]
        )
        assert "Unable to send data to google sheet:" in caplog.text
        assert "Data not written to sheet." in caplog.text

    def test_write_data_to_sheet(self, mocker, caplog):
        mock = mocker.Mock()
        mocker.patch("googleapiclient.discovery.build", mock)
        mocker.patch("googleapiclient.discovery.build_from_document", mock)
        mocker.patch.object(reporter.GoogleSheetsReporter, "configure_sheet", mock)
        self.REPORT_HANDLER.write_report(
            [["BTSERIES", "9781234567890", "12345", "[]", "Foo", "Bar", "False"]]
        )
        assert "Data written to Google Sheet: " in caplog.text


class TestReportService:
    def test_write_output_report(self, mock_sheet_service, caplog):
        WriteOutputReport.execute(
            report_data={
                "total_records": 1,
                "file_names": ["foo.mrc"],
                "total_files": 1,
                "vendor_report": [],
                "duplicate_report": [{"foo": "bar"}],
                "missing_barcodes": [],
                "processing_integrity": True,
                "call_number_report": [{"foo": "bar"}],
            },
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 2
        assert caplog.records[0].message.startswith("Data written to Google Sheet:")
        assert caplog.records[1].message.startswith("Data written to Google Sheet:")

    def test_write_output_report_no_call_no_report(self, mock_sheet_service, caplog):
        WriteOutputReport.execute(
            report_data={
                "total_records": 1,
                "file_names": ["foo.mrc"],
                "total_files": 1,
                "vendor_report": [],
                "duplicate_report": [],
                "missing_barcodes": [],
                "processing_integrity": True,
                "call_number_report": [],
            },
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 1
        assert "Data written to Google Sheet: " in caplog.text
