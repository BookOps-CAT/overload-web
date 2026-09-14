import datetime
import io
import json
from typing import Any

import pytest
import requests
from bookops_worldcat.errors import BookopsWorldcatError
from file_retriever import Client, File, FileInfo

from overload_web.domain.pvf import models
from overload_web.infrastructure import oclc, sierra_clients


@pytest.fixture(autouse=True)
def test_setup(caplog, monkeypatch):
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


@pytest.fixture
def mock_bpl_session_error(monkeypatch, mock_sierra_session):
    def mock_error(*args, **kwargs):
        raise sierra_clients.BookopsSolrError

    monkeypatch.setattr(FakeSierraSession, "_get_bibs_by_isbn", mock_error)
    return FakeSierraSession()


@pytest.fixture
def mock_nypl_session_error(monkeypatch, mock_sierra_session):
    def mock_error(*args, **kwargs):
        raise sierra_clients.BookopsPlatformError

    def mock_nypl_error(*args, **kwargs):
        raise requests.exceptions.Timeout

    monkeypatch.setattr("requests.post", mock_nypl_error)
    monkeypatch.setattr(FakeSierraSession, "_get_bibs_by_isbn", mock_error)
    return FakeSierraSession()


@pytest.fixture
def mock_sftp_client(monkeypatch):
    file_data = {"file_size": 140401, "file_mtime": 1704070800, "file_mode": 33188}

    def _get_file(*args, **kwargs):
        return File.from_fileinfo(file=kwargs["file"], file_stream=io.BytesIO(b""))

    def _get_file_info(*args, **kwargs):
        file_data["file_name"] = kwargs["file_name"]
        return FileInfo(**file_data)

    def _list_files(*args, **kwargs):
        return ["foo.mrc"]

    def _put_file(*args, **kwargs):
        file_data["file_name"] = kwargs["file"].file_name
        return FileInfo(**file_data)

    def null_return(*args, **kwargs):
        return None

    monkeypatch.setattr(Client, "get_file", _get_file)
    monkeypatch.setattr(Client, "get_file_info", _get_file_info)
    monkeypatch.setattr(Client, "list_files", _list_files)
    monkeypatch.setattr(Client, "put_file", _put_file)
    monkeypatch.setattr(Client, "_Client__connect_to_server", null_return)
    return Client(
        name="FOO", username="foo", password="bar", host="sftp.baz.com", port="22"
    )


@pytest.fixture
def stub_template_data() -> dict:
    return {
        "name": "Foo",
        "agent": "Bar",
        "blanket_po": None,
        "copies": "5",
        "country": "xxu",
        "create_date": "2024-01-01",
        "format": "a",
        "fund": "10001adbk",
        "id": 1,
        "internal_note": "foo",
        "lang": "spa",
        "order_code_1": "b",
        "order_code_2": None,
        "order_code_3": "d",
        "order_code_4": "a",
        "order_type": "p",
        "price": "$20.00",
        "selector_note": None,
        "status": "o",
        "var_field_isbn": None,
        "vendor_code": "0049",
        "vendor_notes": "bar",
        "vendor_title_no": None,
        "primary_matchpoint": "isbn",
        "secondary_matchpoint": None,
        "tertiary_matchpoint": None,
    }


@pytest.fixture
def stub_bib():
    def make_bib(library, collection, record_type):
        return models.DomainBib(
            library=library,
            collection=collection,
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

    return make_bib


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
