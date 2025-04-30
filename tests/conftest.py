import io

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from overload_web.domain import match_service, model
from overload_web.infrastructure import orm


@pytest.fixture(autouse=True)
def fake_creds(monkeypatch):
    monkeypatch.setenv("BPL_SOLR_CLIENT", "test")
    monkeypatch.setenv("BPL_SOLR_TARGET", "dev")
    monkeypatch.setenv("NYPL_PLATFORM_CLIENT", "test")
    monkeypatch.setenv("NYPL_PLATFORM_SECRET", "test")
    monkeypatch.setenv("NYPL_PLATFORM_OAUTH", "test")
    monkeypatch.setenv("NYPL_PLATFORM_AGENT", "test")
    monkeypatch.setenv("NYPL_PLATFORM_TARGET", "dev")


@pytest.fixture
def mock_sierra_response(monkeypatch):
    class MockHTTPResponse:
        def __init__(self, status_code: int, ok: bool, stub_json: dict):
            self.status_code = status_code
            self.ok = ok
            self.stub_json = stub_json

        def json(self):
            return self.stub_json

    def mock_response(*args, **kwargs):
        json = {
            "response": {"docs": [{"id": "123456789"}]},
            "data": [{"id": "123456789"}],
        }
        return MockHTTPResponse(status_code=200, ok=True, stub_json=json)

    def mock_token_response(*args, **kwargs):
        token_json = {"access_token": "foo", "expires_in": 10}
        return MockHTTPResponse(status_code=200, ok=True, stub_json=token_json)

    monkeypatch.setattr("requests.Session.get", mock_response)
    monkeypatch.setattr("requests.post", mock_token_response)


@pytest.fixture
def test_fetcher():
    class FakeBibFetcher(match_service.BibFetcher):
        def get_bibs_by_id(self, value, key):
            bib_1 = {"bib_id": "123", "isbn": "9781234567890"}
            bib_2 = {"bib_id": "234", "isbn": "1234567890", "oclc_number": "123456789"}
            bib_3 = {
                "bib_id": "345",
                "isbn": "9781234567890",
                "oclc_number": "123456789",
            }
            bib_4 = {"bib_id": "456", "upc": "333"}
            return [bib_1, bib_2, bib_3, bib_4]

    return FakeBibFetcher()


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    orm.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_sql_session(in_memory_db):
    orm.start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@pytest.fixture
def make_template():
    def _make_template(data, matchpoints):
        template = model.Template(**data)
        matchpoints = model.Matchpoints(**matchpoints)
        template.matchpoints = matchpoints
        return template

    return _make_template


@pytest.fixture
def bib_data(order_data, library) -> dict:
    return {"library": library, "orders": [order_data]}


@pytest.fixture
def order_data() -> dict:
    return {
        "audience": "a",
        "blanket_po": None,
        "copies": "7",
        "country": "xxu",
        "create_date": "2024-01-01",
        "format": "a",
        "fund": "25240adbk",
        "internal_note": None,
        "lang": "eng",
        "locations": ["(4)fwa0f", "(2)bca0f", "gka0f"],
        "order_type": "p",
        "price": "$5.00",
        "selector": "b",
        "selector_note": None,
        "source": "d",
        "status": "o",
        "var_field_isbn": None,
        "vendor_code": "0049",
        "vendor_notes": None,
        "vendor_title_no": None,
    }


@pytest.fixture
def template_data() -> dict:
    return {
        "agent": None,
        "audience": "a",
        "blanket_po": None,
        "copies": "5",
        "country": "xxu",
        "create_date": "2024-01-01",
        "format": "a",
        "fund": "10001adbk",
        "id": None,
        "internal_note": "foo",
        "lang": "spa",
        "name": None,
        "order_type": "p",
        "price": "$20.00",
        "selector": "b",
        "selector_note": None,
        "source": "d",
        "status": "o",
        "var_field_isbn": None,
        "vendor_code": "0049",
        "vendor_notes": "bar",
        "vendor_title_no": None,
        "matchpoints": {
            "primary": "isbn",
            "secondary": None,
            "tertiary": None,
        },
    }


@pytest.fixture
def stub_bib(library) -> Bib:
    bib = Bib()
    bib.leader = "02866pam  2200517 i 4500"
    bib.library = library
    bib.add_field(
        Field(
            tag="020",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value="9781234567890")],
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
                Subfield(code="h", value="baz"),
                Subfield(code="i", value="foo"),
                Subfield(code="l", value="bar"),
                Subfield(code="m", value="baz"),
            ],
        )
    )
    return bib


@pytest.fixture
def stub_binary_marc(stub_bib) -> io.BytesIO:
    return io.BytesIO(stub_bib.as_marc())


@pytest.fixture
def stub_pvf_form_data(template_data, library, destination) -> dict:
    pvf_form_data = {k: v for k, v in template_data.items() if k != "matchpoints"}
    pvf_form_data["primary_matchpoint"] = template_data["matchpoints"]["primary"]
    pvf_form_data["secondary_matchpoint"] = template_data["matchpoints"]["secondary"]
    pvf_form_data["tertiary_matchpoint"] = template_data["matchpoints"]["tertiary"]
    pvf_form_data["library"] = library
    pvf_form_data["destination"] = destination
    return pvf_form_data
