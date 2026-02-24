import pytest

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
def mock_sheet_config(monkeypatch, mocker) -> None:
    m = mocker.mock_open(read_data="")
    mocker.patch("overload_web.infrastructure.reporter.open", m)
    mocker.patch("os.path.exists", lambda *args, **kwargs: True)

    def build_sheet(*args, **kwargs):
        return MockResource()

    def mock_creds(*args, **kwargs):
        return MockCreds()

    monkeypatch.setattr("googleapiclient.discovery.build", build_sheet)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", build_sheet)
    monkeypatch.setattr(
        "google.oauth2.credentials.Credentials.from_authorized_user_info", mock_creds
    )


@pytest.fixture
def mock_sheet_config_expired_creds(monkeypatch, mock_sheet_config):
    monkeypatch.setattr(MockCreds, "valid", False)
    monkeypatch.setattr(MockCreds, "expired", True)


@pytest.fixture
def mock_sheet_config_no_creds(monkeypatch, mock_sheet_config):
    monkeypatch.setattr(
        "google_auth_oauthlib.flow.InstalledAppFlow.from_client_config",
        lambda *args, **kwargs: MockCreds(),
    )
    monkeypatch.setattr(
        "google.oauth2.credentials.Credentials.from_authorized_user_info",
        lambda *args, **kwargs: None,
    )


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
def order_records_dict(sel_bib, sierra_response, pandas_handler):
    analysis = sel_bib.analyze_matches(candidates=[sierra_response])
    sel_bib.apply_match(analysis)
    return pandas_handler.list2dict([sel_bib])


@pytest.fixture
def stub_report(order_records_dict, pandas_handler):
    return pandas_handler.create_duplicate_report(order_records_dict)


@pytest.fixture
def full_records_dict(full_bib, pandas_handler, sierra_response):
    analysis = full_bib.analyze_matches(candidates=[sierra_response])
    full_bib.apply_match(analysis)
    return pandas_handler.list2dict([full_bib])


@pytest.fixture
def full_records_dict_no_call_no_match(full_bib, pandas_handler, sierra_response):
    if full_bib.library == "nypl" and full_bib.collection == "BL":
        sierra_response["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Bar", "tag": "a"}]},
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
        ]
    elif full_bib.library == "nypl" and full_bib.collection == "RL":
        sierra_response["varFields"] = [
            i for i in sierra_response["varFields"] if i["marcTag"] != "852"
        ]
    else:
        sierra_response["call_number"] = "Bar"
    analysis = full_bib.analyze_matches(candidates=[sierra_response])
    full_bib.apply_match(analysis)
    return pandas_handler.list2dict([full_bib])


@pytest.fixture
def pandas_handler(library, collection, record_type):
    return reporter.PandasReportHandler(
        library=library, collection=collection, record_type=record_type
    )


@pytest.mark.parametrize(
    "library, collection, record_type",
    [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
)
class TestOrderRecordsProcessingReports:
    def test_call_number_report(self, order_records_dict, pandas_handler):
        report = pandas_handler.create_call_number_report(
            report_data=order_records_dict
        )
        assert report is None

    def test_detailed_report(self, order_records_dict, pandas_handler):
        report = pandas_handler.create_detailed_report(report_data=order_records_dict)
        assert report["vendor"] == ["BTSERIES"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["target_bib_id"] == ["12345"]
        assert report["updated"] == [False]
        assert report["call_number_match"] == [True]
        assert report["call_number"] == ["Foo"]
        assert report["target_call_no"] == ["Foo"]
        assert report["duplicate_records"] == [[]]
        assert report["mixed"] == [[]]
        assert report["other"] == [[]]

    def test_duplicate_report(self, order_records_dict, pandas_handler):
        report = pandas_handler.create_duplicate_report(order_records_dict)
        assert report["vendor"] == ["BTSERIES"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["target_bib_id"] == ["12345"]
        assert report["duplicate_records"] == [[]]
        assert report["mixed"] == [[]]
        assert report["other"] == [[]]

    def test_summary_report(
        self, order_records_dict, pandas_handler, library, collection, record_type
    ):
        report = pandas_handler.create_summary_report(
            file_names=["foo.mrc"],
            total_files_processed=1,
            total_records_processed=1,
            report_data=order_records_dict,
        )
        assert report["library"] == [library]
        assert report["collection"] == [collection]
        assert report["record_type"] == [record_type]
        assert report["file_names"] == [["foo.mrc"]]
        assert report["total_files_processed"] == [1]
        assert report["total_records_processed"] == [1]
        assert report["missing_barcodes"] == [[]]
        assert report["processing_integrity"] == [None]
        assert report["vendor_breakdown"] == {
            "attach": [1],
            "insert": [0],
            "update": [0],
            "total": [1],
            "vendor": ["BTSERIES"],
        }
        assert report["duplicates_report"] == {
            "vendor": ["BTSERIES"],
            "resource_id": ["9781234567890"],
            "target_bib_id": ["12345"],
            "duplicate_records": [[]],
            "mixed": [[]],
            "other": [[]],
        }
        assert report["call_number_issues"] is None

    def test_vendor_report(self, order_records_dict, pandas_handler):
        report = pandas_handler.create_vendor_report(order_records_dict)
        assert report["vendor"] == ["BTSERIES"]
        assert report["attach"] == [1]
        assert report["insert"] == [0]
        assert report["update"] == [0]
        assert report["total"] == [1]


@pytest.mark.parametrize(
    "library, collection, record_type",
    [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
)
class TestFullRecordsProcessingReports:
    def test_call_number_report(
        self, full_records_dict_no_call_no_match, pandas_handler
    ):
        report = pandas_handler.create_call_number_report(
            report_data=full_records_dict_no_call_no_match
        )
        assert report["vendor"] == ["UNKNOWN"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["duplicate_records"] == [[]]
        assert report["call_number_match"] == [False]
        assert report["call_number"] == ["Foo"]
        assert report["target_call_no"] != ["Foo"]

    def test_detailed_report(self, full_records_dict, pandas_handler):
        report = pandas_handler.create_detailed_report(report_data=full_records_dict)
        assert report["vendor"] == ["UNKNOWN"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["target_bib_id"] == ["12345"]
        assert report["updated"] == [False]
        assert report["call_number_match"] == [True]
        assert report["call_number"] == ["Foo"]
        assert report["target_call_no"] == ["Foo"]
        assert report["duplicate_records"] == [[]]
        assert report["mixed"] == [[]]
        assert report["other"] == [[]]

    def test_duplicate_report(self, full_records_dict, pandas_handler):
        report = pandas_handler.create_duplicate_report(full_records_dict)
        assert report["vendor"] == ["UNKNOWN"]
        assert report["resource_id"] == ["9781234567890"]
        assert report["target_bib_id"] == ["12345"]
        assert report["duplicate_records"] == [[]]
        assert report["mixed"] == [[]]
        assert report["other"] == [[]]

    def test_summary_report(
        self, full_records_dict, pandas_handler, library, collection, record_type
    ):
        report = pandas_handler.create_summary_report(
            file_names=["foo.mrc"],
            total_files_processed=1,
            total_records_processed=1,
            report_data=full_records_dict,
        )
        assert report["library"] == [library]
        assert report["collection"] == [collection]
        assert report["record_type"] == [record_type]
        assert report["file_names"] == [["foo.mrc"]]
        assert report["total_files_processed"] == [1]
        assert report["total_records_processed"] == [1]
        assert report["missing_barcodes"] == [[]]
        assert report["processing_integrity"] == [None]
        assert report["vendor_breakdown"] == {
            "attach": [1],
            "insert": [0],
            "update": [0],
            "total": [1],
            "vendor": ["UNKNOWN"],
        }
        assert report["duplicates_report"] == {
            "vendor": ["UNKNOWN"],
            "resource_id": ["9781234567890"],
            "target_bib_id": ["12345"],
            "duplicate_records": [[]],
            "mixed": [[]],
            "other": [[]],
        }
        assert report["call_number_issues"] is None

    def test_vendor_report(self, full_records_dict, pandas_handler):
        report = pandas_handler.create_vendor_report(full_records_dict)
        assert report["vendor"] == ["UNKNOWN"]
        assert report["attach"] == [1]
        assert report["insert"] == [0]
        assert report["update"] == [0]
        assert report["total"] == [1]
