import copy
import io
import logging
import os
from typing import Any, Callable

import pytest
import requests
from bookops_marc import Bib
from file_retriever import Client, File, FileInfo
from pymarc import Field, Indicators, Subfield
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application import dto
from overload_web.domain import models
from overload_web.infrastructure import bibs, db


@pytest.fixture(autouse=True)
def set_caplog_level(caplog):
    caplog.set_level("DEBUG")
    logger = logging.getLogger("overload_web")
    for handler in logger.handlers:
        if not isinstance(handler, logging.StreamHandler):
            logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def fake_creds(monkeypatch):
    monkeypatch.setenv("BPL_SOLR_CLIENT", "test")
    monkeypatch.setenv("BPL_SOLR_TARGET", "dev")
    monkeypatch.setenv("NYPL_PLATFORM_CLIENT", "test")
    monkeypatch.setenv("NYPL_PLATFORM_SECRET", "test")
    monkeypatch.setenv("NYPL_PLATFORM_OAUTH", "test")
    monkeypatch.setenv("NYPL_PLATFORM_AGENT", "test")
    monkeypatch.setenv("NYPL_PLATFORM_TARGET", "dev")
    monkeypatch.setenv("LOGGLY_TOKEN", "foo")
    monkeypatch.setenv("FOO_USER", "foo")
    monkeypatch.setenv("FOO_PASSWORD", "bar")
    monkeypatch.setenv("FOO_HOST", "sftp.baz.com")
    monkeypatch.setenv("FOO_PORT", "22")
    monkeypatch.setenv("FOO_SRC", "/")
    monkeypatch.setenv("FOO_DST", "nsdrop/vendor_files/foo")
    monkeypatch.setenv("NSDROP_USER", "foo")
    monkeypatch.setenv("NSDROP_PASSWORD", "bar")
    monkeypatch.setenv("NSDROP_HOST", "sftp.baz.com")
    monkeypatch.setenv("NSDROP_PORT", "22")
    monkeypatch.setenv("NSDROP_SRC", "/")
    monkeypatch.setenv("NSDROP_DST", "nsdrop/vendor_files/bar")


@pytest.fixture
def test_sql_session():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def make_template():
    def _make_template(data):
        template = db.tables.OrderTemplate(**data)
        return template

    return _make_template


class MockHTTPResponse:
    def __init__(self, status_code: int, ok: bool, stub_json: dict):
        self.status_code = status_code
        self.ok = ok
        self.stub_json = stub_json

    def json(self):
        return self.stub_json


@pytest.fixture
def mock_sierra_response(monkeypatch):
    def mock_response(*args, **kwargs):
        stub_record = {"id": "123456789", "title": "foo"}
        json = {
            "response": {"docs": [stub_record]},
            "data": [stub_record],
        }
        return MockHTTPResponse(status_code=200, ok=True, stub_json=json)

    def mock_token_response(*args, **kwargs):
        token_json = {"access_token": "foo", "expires_in": 10}
        return MockHTTPResponse(status_code=200, ok=True, stub_json=token_json)

    monkeypatch.setattr("requests.Session.get", mock_response)
    monkeypatch.setattr("requests.post", mock_token_response)


@pytest.fixture
def mock_sierra_no_response(mock_sierra_response, monkeypatch):
    def response_none(*args, **kwargs):
        json = {"response": {"docs": []}, "data": []}
        return MockHTTPResponse(status_code=200, ok=True, stub_json=json)

    monkeypatch.setattr("requests.Session.get", response_none)


@pytest.fixture
def mock_sierra_nypl_auth_error(monkeypatch, mock_sierra_response):
    def mock_nypl_error(*args, **kwargs):
        raise requests.exceptions.Timeout

    monkeypatch.setattr("requests.post", mock_nypl_error)


@pytest.fixture
def mock_sierra_error(monkeypatch, mock_sierra_response):
    def mock_nypl_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError

    monkeypatch.setattr("requests.Session.get", mock_nypl_error)


class FakeSierraSession(bibs.sierra.SierraSessionProtocol):
    def __init__(self) -> None:
        self.credentials = self._get_credentials()


class FakeSierraResponse(models.responses.BaseSierraResponse):
    library = "library"

    @property
    def barcodes(self) -> list[str]:
        return ["333331234567890"]

    @property
    def branch_call_no(self) -> list[str]:
        return ["FIC"]

    @property
    def cat_source(self) -> str:
        return "inhouse"

    @property
    def collection(self) -> str | None:
        return None

    @property
    def isbn(self) -> list[str]:
        return [self._data["id"]]

    @property
    def oclc_number(self) -> list[str]:
        return [self._data["id"]]

    @property
    def research_call_no(self) -> list[str]:
        return ["FOO"]

    @property
    def upc(self) -> list[str]:
        return [self._data["id"]]

    @property
    def update_date(self) -> str | None:
        return None

    @property
    def var_fields(self) -> list[dict[str, Any]]:
        return [{"020": self._data["id"]}]


@pytest.fixture
def mock_session(monkeypatch, mock_sierra_response):
    def mock_response(*args, **kwargs):
        return [FakeSierraResponse({"id": "123456789", "title": "foo"})]

    monkeypatch.setattr(
        bibs.sierra.SierraSessionProtocol, "_parse_response", mock_response
    )
    return FakeSierraSession()


@pytest.fixture
def mock_session_no_response():
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

    monkeypatch.setattr(Client, "get_file", _get_file)
    monkeypatch.setattr(Client, "get_file_info", _get_file_info)
    monkeypatch.setattr(Client, "list_files", _list_files)
    monkeypatch.setattr(Client, "put_file", _put_file)
    monkeypatch.setattr(
        Client, "_Client__connect_to_server", lambda *args, **kwargs: None
    )
    return Client(
        name="FOO",
        username=os.environ["FOO_USER"],
        password=os.environ["FOO_PASSWORD"],
        host=os.environ["FOO_HOST"],
        port=os.environ["FOO_PORT"],
    )


@pytest.fixture
def order_data() -> dict:
    return {
        "audience": ["a", "a", "a"],
        "blanket_po": None,
        "branches": ["fw", "bc", "gk"],
        "copies": "7",
        "country": "xxu",
        "create_date": "2024-01-01",
        "format": "a",
        "fund": "25240adbk",
        "internal_note": None,
        "lang": "eng",
        "locations": ["(4)fwa0f", "(2)bca0f", "gka0f"],
        "order_code_1": "b",
        "order_code_2": None,
        "order_code_3": "d",
        "order_code_4": "a",
        "order_id": 1234567,
        "order_type": "p",
        "price": "$5.00",
        "selector_note": None,
        "shelves": ["0f", "0f", "0f"],
        "status": "o",
        "vendor_code": "0049",
        "vendor_notes": None,
        "vendor_title_no": None,
    }


@pytest.fixture
def template_data() -> dict:
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
def stub_bib(library) -> Bib:
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    if library == "bpl":
        bib.add_field(
            Field(
                tag="037",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="123"),
                    Subfield(code="b", value="OverDrive, Inc."),
                ],
            )
        )
    bib.add_field(
        Field(
            tag="949",
            indicators=Indicators(" ", "1"),
            subfields=[
                Subfield(code="i", value="333331234567890"),
            ],
        )
    )
    bib.add_field(
        Field(
            tag="960",
            indicators=Indicators(" ", " "),
            subfields=[
                Subfield(code="a", value="l"),
                Subfield(code="b", value="-"),
                Subfield(code="c", value="j"),
                Subfield(code="d", value="c"),
                Subfield(code="e", value="d"),
                Subfield(code="f", value="a"),
                Subfield(code="g", value="b"),
                Subfield(code="h", value="-"),
                Subfield(code="i", value="l"),
                Subfield(code="j", value="-"),
                Subfield(code="m", value="o"),
                Subfield(code="n", value="-"),
                Subfield(code="o", value="13"),
                Subfield(code="p", value="  -  -  "),
                Subfield(code="q", value="01-01-25"),
                Subfield(code="r", value="  -  -  "),
                Subfield(code="s", value="{{dollar}}13.20"),
                Subfield(code="t", value="agj0y"),
                Subfield(code="u", value="lease"),
                Subfield(code="v", value="btlea"),
                Subfield(code="w", value="eng"),
                Subfield(code="x", value="xxu"),
                Subfield(code="y", value="1"),
                Subfield(code="z", value=".o10000010"),
            ],
        )
    )
    bib.add_field(
        Field(
            tag="961",
            indicators=Indicators(" ", " "),
            subfields=[
                Subfield(code="d", value="foo"),
                Subfield(code="f", value="bar"),
                Subfield(code="m", value="baz"),
            ],
        )
    )
    return bib


@pytest.fixture
def make_bib_dto(stub_bib) -> Callable:
    def _make_dto(data: dict[str, dict[str, str]]):
        record = copy.deepcopy(stub_bib)
        for k, v in data.items():
            record.add_field(
                Field(
                    tag=k,
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code=v["code"], value=v["value"]),
                    ],
                )
            )
        mapper = bibs.marc.BookopsMarcMapper()
        return dto.BibDTO(bib=record, domain_bib=mapper.map_bib(record))

    return _make_dto
