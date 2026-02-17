import datetime
import io
import json
import logging
from typing import Any

import pytest
import requests
from bookops_marc import Bib
from file_retriever import Client, File, FileInfo
from pymarc import Field, Indicators, Subfield

from overload_web.domain.models import bibs, sierra_responses
from overload_web.infrastructure import clients
from overload_web.infrastructure import marc_engine as engine


@pytest.fixture(scope="session")
def get_constants() -> dict[str, Any]:
    """Retrieve processing constants from JSON file."""
    with open("overload_web/data/mapping_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


@pytest.fixture(autouse=True)
def test_setup(caplog, monkeypatch):
    caplog.set_level("DEBUG")
    logger = logging.getLogger("overload_web")
    for handler in logger.handlers:
        if not isinstance(handler, logging.StreamHandler):
            logger.removeHandler(handler)
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


class MockHTTPResponse:
    def __init__(self, status_code: int, ok: bool, _json: dict):
        self.status_code = status_code
        self.ok = ok
        self._json = _json

    def json(self):
        return self._json


class FakeSierraResponse(sierra_responses.BaseSierraResponse):
    library = "library"

    @property
    def barcodes(self) -> list[str]:
        return ["333331234567890"]

    @property
    def branch_call_number(self) -> str | None:
        return "FIC"

    @property
    def cat_source(self) -> str:
        return "inhouse"

    @property
    def collection(self) -> str | None:
        return None

    @property
    def control_number(self) -> str | None:
        return self._data["id"]

    @property
    def isbn(self) -> list[str]:
        return [self._data["id"]]

    @property
    def oclc_number(self) -> list[str]:
        return [self._data["id"]]

    @property
    def research_call_number(self) -> list[str]:
        return ["FOO"]

    @property
    def upc(self) -> list[str]:
        return [self._data["id"]]

    @property
    def update_date(self) -> str:
        return "2025-01-01T00:00:00"

    @property
    def update_datetime(self) -> datetime.datetime:
        return datetime.datetime(2025, 1, 1, 0, 0, 0)

    @property
    def var_fields(self) -> list[dict[str, Any]]:
        return [{"020": self._data["id"]}]


class FakeSierraSession(clients.SierraSessionProtocol):
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

    def _parse_response(
        self, response: requests.Response
    ) -> list[sierra_responses.BaseSierraResponse]:
        return [FakeSierraResponse({"id": "123456789", "title": "foo"})]


@pytest.fixture
def mock_session(monkeypatch):
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
def mock_bpl_session_error(monkeypatch, mock_session):
    def mock_error(*args, **kwargs):
        raise clients.BookopsSolrError

    monkeypatch.setattr(FakeSierraSession, "_get_bibs_by_isbn", mock_error)
    return FakeSierraSession()


@pytest.fixture
def mock_nypl_session_error(monkeypatch, mock_session):
    def mock_error(*args, **kwargs):
        raise clients.BookopsPlatformError

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
def fake_template_data() -> dict:
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
def stub_bib(library, collection) -> Bib:
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    bib.add_field(Field(tag="005", data="20200101010000.0"))
    bib.add_field(
        Field(
            tag="020",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value="9781234567890")],
        )
    )
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
                tag="099",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="Foo"),
                ],
            )
        )
    else:
        if collection == "BL":
            bib.add_field(
                Field(
                    tag="091",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        else:
            bib.add_field(
                Field(
                    tag="852",
                    indicators=Indicators("8", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        bib.add_field(
            Field(
                tag="910",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=collection)],
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
                Subfield(code="k", value="A01"),
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
def acq_bib(collection, library):
    order = bibs.Order(
        locations=["agj0y"],
        audience=["j"],
        branches=["ag"],
        copies="13",
        create_date="01-01-25",
        format="b",
        lang="eng",
        order_id=".o10000010",
        shelves=["0y"],
        status="o",
        vendor_notes=None,
        order_code_1="j",
        order_code_2="c",
        order_code_3="d",
        order_code_4="a",
        order_type="l",
        price="{{dollar}}13.20",
        project_code="A01",
        fund="lease",
        vendor_code="btlea",
        country="xxu",
        internal_note="foo",
        selector_note="bar",
        vendor_title_no=None,
        blanket_po="baz",
    )
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    bib.add_field(Field(tag="005", data="20200101010000.0"))
    bib.add_field(
        Field(
            tag="020",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value="9781234567890")],
        )
    )
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
                tag="099",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="Foo"),
                ],
            )
        )
    else:
        if collection == "BL":
            bib.add_field(
                Field(
                    tag="091",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        else:
            bib.add_field(
                Field(
                    tag="852",
                    indicators=Indicators("8", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        bib.add_field(
            Field(
                tag="910",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=collection)],
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
                Subfield(code="c", value=order.order_code_1),
                Subfield(code="d", value=order.order_code_2),
                Subfield(code="e", value=order.order_code_3),
                Subfield(code="f", value=order.order_code_4),
                Subfield(code="g", value=order.format),
                Subfield(code="i", value=order.order_type),
                Subfield(code="m", value=order.status),
                Subfield(code="o", value=order.copies),
                Subfield(code="q", value=order.create_date),
                Subfield(code="s", value=order.price),
                Subfield(code="t", value=order.locations[0]),
                Subfield(code="u", value=order.fund),
                Subfield(code="v", value=order.vendor_code),
                Subfield(code="w", value=order.lang),
                Subfield(code="x", value=order.country),
                Subfield(code="z", value=order.order_id),
            ],
        )
    )
    bib.add_field(
        Field(
            tag="961",
            indicators=Indicators(" ", " "),
            subfields=[
                Subfield(code="d", value=order.internal_note),
                Subfield(code="f", value=order.selector_note),
                Subfield(code="m", value=order.blanket_po),
            ],
        )
    )
    domain_bib = bibs.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type="acq",
        binary_data=bib.as_marc(),
        branch_call_number="Foo",
        research_call_number=["Foo"],
        vendor="BTSERIES",
        barcodes=["333331234567890"],
        orders=[order],
        update_date="20200101010000.0",
    )
    return domain_bib


@pytest.fixture
def sel_bib(collection, library):
    order = bibs.Order(
        locations=["agj0y"],
        audience=["j"],
        branches=["ag"],
        copies="13",
        create_date="01-01-25",
        format="b",
        lang="eng",
        order_id=".o10000010",
        shelves=["0y"],
        status="o",
        vendor_notes=None,
        order_code_1="j",
        order_code_2="c",
        order_code_3="d",
        order_code_4="a",
        order_type="l",
        price="{{dollar}}13.20",
        project_code="A01",
        fund="lease",
        vendor_code="btlea",
        country="xxu",
        internal_note="foo",
        selector_note="bar",
        vendor_title_no=None,
        blanket_po="baz",
    )
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    bib.add_field(Field(tag="005", data="20200101010000.0"))
    bib.add_field(
        Field(
            tag="020",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value="9781234567890")],
        )
    )
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
                tag="099",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="Foo"),
                ],
            )
        )
    else:
        if collection == "BL":
            bib.add_field(
                Field(
                    tag="091",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        else:
            bib.add_field(
                Field(
                    tag="852",
                    indicators=Indicators("8", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        bib.add_field(
            Field(
                tag="910",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=collection)],
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
                Subfield(code="c", value=order.order_code_1),
                Subfield(code="d", value=order.order_code_2),
                Subfield(code="e", value=order.order_code_3),
                Subfield(code="f", value=order.order_code_4),
                Subfield(code="g", value=order.format),
                Subfield(code="i", value=order.order_type),
                Subfield(code="m", value=order.status),
                Subfield(code="o", value=order.copies),
                Subfield(code="q", value=order.create_date),
                Subfield(code="s", value=order.price),
                Subfield(code="t", value=order.locations[0]),
                Subfield(code="u", value=order.fund),
                Subfield(code="v", value=order.vendor_code),
                Subfield(code="w", value=order.lang),
                Subfield(code="x", value=order.country),
                Subfield(code="z", value=order.order_id),
            ],
        )
    )
    bib.add_field(
        Field(
            tag="961",
            indicators=Indicators(" ", " "),
            subfields=[
                Subfield(code="d", value=order.internal_note),
                Subfield(code="f", value=order.selector_note),
                Subfield(code="m", value=order.blanket_po),
            ],
        )
    )
    domain_bib = bibs.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type="acq",
        binary_data=bib.as_marc(),
        branch_call_number="Foo",
        research_call_number=["Foo"],
        vendor="BTSERIES",
        barcodes=["333331234567890"],
        orders=[order],
        update_date="20200101010000.0",
    )
    return domain_bib


@pytest.fixture
def full_bib(library, collection):
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    bib.add_field(Field(tag="005", data="20200101010000.0"))
    bib.add_field(
        Field(
            tag="020",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value="9781234567890")],
        )
    )
    if library == "bpl":
        bib.add_field(
            Field(
                tag="099",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="Foo"),
                ],
            )
        )
        bib.add_field(
            Field(
                tag="960",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="i", value="333331234567890"),
                ],
            )
        )
    else:
        if collection == "BL":
            bib.add_field(
                Field(
                    tag="091",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        else:
            bib.add_field(
                Field(
                    tag="852",
                    indicators=Indicators("8", " "),
                    subfields=[
                        Subfield(code="a", value="Foo"),
                    ],
                )
            )
        bib.add_field(
            Field(
                tag="910",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=collection)],
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
    domain_bib = bibs.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type="cat",
        binary_data=bib.as_marc(),
        branch_call_number="Foo",
        research_call_number=["Foo"],
        barcodes=["333331234567890"],
        orders=[],
        update_date="20200101010000.0",
        vendor_info=bibs.VendorInfo(
            name="UNKNOWN",
            bib_fields=[],
            matchpoints={
                "primary_matchpoint": "isbn",
                "secondary_matchpoint": "oclc_number",
            },
        ),
    )
    return domain_bib


@pytest.fixture
def sierra_response(library, collection):
    if library == "bpl":
        data = {
            "call_number": "Foo",
            "id": "12345",
            "isbn": ["9781234567890"],
            "sm_bib_varfields": ["099 || {{a}} Foo"],
            "sm_item_data": ['{"barcode": "33333123456789"}'],
            "ss_marc_tag_001": "ocn123456789",
            "ss_marc_tag_003": "OCoLC",
            "ss_marc_tag_005": "20000101010000.0",
            "title": "Record 1",
        }
        return sierra_responses.BPLSolrResponse(data=data)

    call_no_field = {"content": "Foo", "tag": "a"}
    data = {
        "id": "12345",
        "controlNumber": "ocn123456789",
        "standardNumbers": ["9781234567890"],
        "title": "Record 1",
        "updatedDate": "2000-01-01T01:00:00",
        "varFields": [
            {"marcTag": "091", "subfields": [call_no_field]},
            {"marcTag": "852", "ind1": "8", "ind2": " ", "subfields": [call_no_field]},
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]},
        ],
    }
    return sierra_responses.NYPLPlatformResponse(data=data)


@pytest.fixture
def fake_fetcher(monkeypatch, sierra_response):
    def fake_response(*args, **kwargs):
        return [sierra_response]

    monkeypatch.setattr(FakeSierraSession, "_parse_response", fake_response)
    return clients.SierraBibFetcher(session=FakeSierraSession())


@pytest.fixture
def fake_fetcher_no_matches(monkeypatch):
    def fake_response(*args, **kwargs):
        return []

    monkeypatch.setattr(FakeSierraSession, "_parse_response", fake_response)
    return clients.SierraBibFetcher(session=FakeSierraSession())


@pytest.fixture
def engine_config(
    library, record_type, collection, get_constants
) -> engine.MarcEngineConfig:
    return engine.MarcEngineConfig(
        marc_order_mapping=get_constants["marc_order_mapping"],
        default_loc=get_constants["default_locations"][library].get(collection),
        bib_id_tag=get_constants["bib_id_tag"][library],
        library=library,
        record_type=record_type,
        collection=collection,
        parser_bib_mapping=get_constants["bib_domain_mapping"],
        parser_order_mapping=get_constants["order_domain_mapping"],
        parser_vendor_mapping=get_constants["vendor_info_options"][library],
    )


@pytest.fixture
def marc_engine(engine_config) -> engine.MarcEngine:
    return engine.MarcEngine(rules=engine_config)
