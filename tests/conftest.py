import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.adapters.sierra_adapters import (
    AbstractSierraSession,
    SierraService,
)
from overload_web.domain.model import Order, OrderBib, Template


class MockSierraAdapter(AbstractSierraSession):
    def _get_credentials(self):
        pass

    def _get_target(self):
        pass

    def _get_bibs_by_id(self, key, value):
        if key and value:
            return ["123456789"]
        else:
            return []


@pytest.fixture
def stub_sierra_service(library, monkeypatch):
    def mock_adapter(*args, **kwargs):
        return MockSierraAdapter()

    monkeypatch.setattr(
        "overload_web.adapters.sierra_adapters.BPLSolrSession", mock_adapter
    )
    monkeypatch.setattr(
        "overload_web.adapters.sierra_adapters.NYPLPlatformSession", mock_adapter
    )
    service = SierraService(MockSierraAdapter())
    return service


class MockHTTPResponse:
    def __init__(self, stub_json: dict):
        self.stub_json = stub_json

    def json(self):
        return self.stub_json


@pytest.fixture
def mock_st_post_response(monkeypatch):
    def mock_response(*args, **kwargs):
        stub_json = {
            "order": {"library": "nypl"},
            "template": {
                "fund": "foo",
                "primary_matchpoint": "foo",
                "secondary_matchpoint": "bar",
                "tertiary_matchpoint": "baz",
            },
        }
        return MockHTTPResponse(stub_json=stub_json)

    monkeypatch.setattr("requests.post", mock_response)
    monkeypatch.setenv("API_URL_BASE", "foo")


@pytest.fixture
def stub_order():
    return Order(
        create_date="2024-01-01",
        locations=["(4)fwa0f", "(2)bca0f", "gka0f"],
        price="$5.00",
        fund="25240adbk",
        copies="7",
        lang="eng",
        country="xxu",
        vendor_code="0049",
        format="a",
        selector="b",
        selector_note=None,
        audience="a",
        source="d",
        order_type="p",
        status="o",
        internal_note=None,
        var_field_isbn=None,
        vendor_notes=None,
        vendor_title_no=None,
        blanket_po=None,
    )


@pytest.fixture
def stub_template():
    return Template(
        create_date="2024-01-01",
        price="$20.00",
        fund="10001adbk",
        copies="5",
        lang="spa",
        country="xxu",
        vendor_code="0049",
        format="a",
        selector="b",
        audience="a",
        source="d",
        order_type="p",
        status="o",
        internal_note="foo",
        var_field_isbn=None,
        vendor_notes="bar",
        vendor_title_no=None,
        blanket_po=None,
        primary_matchpoint="isbn",
        secondary_matchpoint=None,
        tertiary_matchpoint=None,
    )


@pytest.fixture
def stub_orderbib(stub_order, library):
    return OrderBib(library=library, orders=[stub_order])


@pytest.fixture
def stub_960():
    return Field(
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


@pytest.fixture
def stub_961():
    return Field(
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


@pytest.fixture
def stub_bib(library, stub_960, stub_961):
    bib = Bib()
    bib.leader = "02866pam  2200517 i 4500"
    bib.library = library
    bib.add_field(stub_960)
    bib.add_field(stub_961)
    return bib


@pytest.fixture
def stub_pvf_form_data(stub_template, library, destination) -> dict:
    form_dict = stub_template.__dict__
    form_dict["library"] = library
    form_dict["destination"] = destination
    return form_dict
