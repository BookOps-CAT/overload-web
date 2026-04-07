import pytest

from overload_web.domain.models import bibs
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

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_write_report(self, mock_sheet_config, stub_report, caplog):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report)
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_write_data_to_sheet_timeout_error(
        self, mock_sheet_config, mock_sheet_timeout_error, stub_report, caplog
    ):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report)
        assert "Unable to send data to google sheet:" in caplog.text
        assert "Data not written to sheet." in caplog.text

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_write_data_to_sheet_auth_error(
        self, mock_sheet_config, mock_sheet_auth_error, stub_report, caplog
    ):
        google_handler = reporter.GoogleSheetsReporter()
        google_handler.write_report(stub_report)
        assert "Unable to configure google sheet API credentials:" in caplog.text
        assert "Data not written to sheet." in caplog.text


@pytest.fixture
def stub_report(sel_bib, sierra_response, record_type):
    analysis = sel_bib.analyze_matches(candidates=[sierra_response])
    sel_bib.apply_match(analysis)
    return bibs.ProcessedFileBatch(
        files={"foo.mrc": b""},
        report=bibs.ProcessingStatistics(
            file_names=["foo.mrc"],
            total_files=1,
            total_records=1,
            vendor=["BTSERIES"],
            resource_id=[sel_bib.analysis.resource_id],
            target_bib_id=[sel_bib.analysis.target_bib_id],
            duplicate_records=[sel_bib.analysis.duplicate_records],
            mixed=[sel_bib.analysis.mixed],
            other=[sel_bib.analysis.other],
            call_number_match=[sel_bib.analysis.call_number_match],
            call_number=[sel_bib.call_number],
            target_call_no=[sel_bib.analysis.target_call_no],
            target_title=[sel_bib.analysis.target_title],
            updated_by_vendor=[sel_bib.analysis.updated_by_vendor],
            action=sel_bib.analysis.action,
        ),
    )


@pytest.fixture
def pandas_handler():
    return reporter.PandasReportHandler()


@pytest.mark.parametrize(
    "library, collection, record_type",
    [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
)
class TestRecordsProcessingReports:
    def test_call_number_report(self, stub_report, pandas_handler, record_type):
        report = pandas_handler.create_call_number_report(
            stub_report.report.call_number_report_data, record_type=record_type
        )
        assert report is None

    def test_duplicate_report(self, stub_report, pandas_handler):
        report = pandas_handler.create_duplicate_report(
            stub_report.report.duplicate_report_data
        )
        assert report["vendor"] == ["BTSERIES"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["target_bib_id"] == ["12345"]
        assert report["duplicate_records"] == [[]]
        assert report["mixed"] == [[]]
        assert report["other"] == [[]]

    def test_vendor_report(self, stub_report, pandas_handler):
        report = pandas_handler.create_vendor_report(
            stub_report.report.vendor_report_data
        )
        assert report["vendor"] == ["BTSERIES"]
        assert report["attach"] == [1]
        assert report["insert"] == [0]
        assert report["update"] == [0]
        assert report["total"] == [1]
