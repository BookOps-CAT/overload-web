import pytest

from overload_web.application.services import report_services
from overload_web.domain.models import reporting
from overload_web.infrastructure import reporter


@pytest.fixture
def mock_sheet_config_invalid_creds(monkeypatch, mock_sheet_config):
    def mock_error(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr(
        "google.oauth2.credentials.Credentials.from_authorized_user_info", mock_error
    )


@pytest.fixture
def mock_sheet_timeout_error(monkeypatch):
    def mock_error(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr("googleapiclient.discovery.build", mock_error)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", mock_error)


@pytest.fixture
def mock_sheet_auth_error(monkeypatch):
    def mock_error(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr("googleapiclient.discovery.build", mock_error)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", mock_error)


@pytest.fixture
def stub_report():
    return reporting.ProcessingStatistics(
        file_names=["foo.mrc"],
        total_files=1,
        total_records=1,
        vendor=["BTSERIES"],
        resource_id=["9781234567890"],
        target_bib_id=["12345"],
        duplicate_records=[[]],
        mixed=[[]],
        other=[[]],
        call_number_match=[False],
        call_number=["Foo"],
        target_call_no=["Bar"],
        target_title=["Baz"],
        updated_by_vendor=[False],
        action="attach",
    )


@pytest.fixture
def pandas_handler():
    return reporter.PandasReportHandler()


class TestReporter:
    def test_configure_sheet(self, mock_sheet_config):
        handler = reporter.GoogleSheetsReporter()
        assert handler.creds.token == "foo"
        assert handler.creds.valid is True
        assert handler.creds.expired is False
        assert handler.creds.refresh_token is not None

    def test_configure_sheet_expired(self, mock_sheet_config_expired_creds):
        handler = reporter.GoogleSheetsReporter()
        assert handler.creds.token == "foo"
        assert handler.creds.valid is True
        assert handler.creds.expired is False
        assert handler.creds.refresh_token is not None

    def test_configure_sheet_generate_new_creds(
        self, mock_sheet_config_no_creds, caplog
    ):
        handler = reporter.GoogleSheetsReporter()
        assert handler.creds.token == "foo"
        assert handler.creds.valid is True
        assert handler.creds.expired is False
        assert handler.creds.refresh_token is not None
        assert "API token not found. Running credential config flow." in caplog.text

    def test_configure_sheet_no_creds(self, mock_sheet_config_no_creds, caplog):
        handler = reporter.GoogleSheetsReporter()
        assert handler.creds.token == "foo"
        assert handler.creds.valid is True
        assert handler.creds.expired is False
        assert handler.creds.refresh_token is not None
        assert "API token not found. Running credential config flow." in caplog.text

    def test_configure_sheet_invalid_creds(
        self, mock_sheet_config_invalid_creds, caplog
    ):
        with pytest.raises(ValueError):
            reporter.GoogleSheetsReporter()

    def test_write_report(self, mock_sheet_config, stub_report, caplog):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report)
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    def test_write_data_to_sheet_timeout_error(
        self, mock_sheet_config, mock_sheet_timeout_error, stub_report, caplog
    ):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report)
        assert "Unable to send data to google sheet:" in caplog.text
        assert "Data not written to sheet." in caplog.text

    def test_write_data_to_sheet_auth_error(
        self, mock_sheet_config, mock_sheet_auth_error, stub_report, caplog
    ):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report)
        assert "Unable to configure google sheet API credentials:" in caplog.text
        assert "Data not written to sheet." in caplog.text


class TestRecordsProcessingReports:
    def test_call_number_report(self, stub_report, pandas_handler):
        report = pandas_handler.create_call_number_report(
            stub_report.call_number_report_data, record_type="sel"
        )
        assert report is not None

    def test_call_number_report_no_issues(self, stub_report, pandas_handler):
        stub_report.call_number_match = [True]
        report = pandas_handler.create_call_number_report(
            stub_report.call_number_report_data, record_type="sel"
        )
        assert report is None

    def test_duplicate_report(self, stub_report, pandas_handler):
        report = pandas_handler.create_duplicate_report(
            stub_report.duplicate_report_data
        )
        assert report["vendor"] == ["BTSERIES"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["target_bib_id"] == ["12345"]
        assert report["duplicate_records"] == [[]]
        assert report["mixed"] == [[]]
        assert report["other"] == [[]]

    def test_vendor_report(self, stub_report, pandas_handler):
        report = pandas_handler.create_vendor_report(stub_report.vendor_report_data)
        assert report["vendor"] == ["BTSERIES"]
        assert report["attach"] == [1]
        assert report["insert"] == [0]
        assert report["update"] == [0]
        assert report["total"] == [1]

    def test_create_detailed_report(self, stub_report):
        out = report_services.PVFReporter.create_detailed_report(
            data=stub_report.__dict__, handler=reporter.PandasReportHandler()
        )
        assert "vendor" in out.keys()
        assert "target_bib_id" in out.keys()
        assert "resource_id" in out.keys()

    def test_create_output_report(self, stub_report):
        out = report_services.PVFReporter.create_output_report(
            data=stub_report.__dict__,
            handler=reporter.PandasReportHandler(),
            record_type="sel",
        )
        assert "vendor_report" in out.keys()
        assert "dupes_report" in out.keys()
        assert "call_no_report" in out.keys()
