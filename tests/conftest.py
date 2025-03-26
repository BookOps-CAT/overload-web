import pytest

from overload_web.adapters.sierra_adapters import (
    AbstractSierraSession,
    SierraService,
)
from overload_web.domain.model import Order, OrderTemplate


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
def stub_order(library):
    return Order(
        library=library,
        create_date="2024-01-01",
        locations=["(4)fwa0f", "(2)bca0f", "gka0f"],
        shelves=["0f", "0f", "0f"],
        price="$5.00",
        fund="25240adbk",
        copies="7",
        lang="eng",
        country="xxu",
        vendor_code="0049",
        format="a",
        selector="b",
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
    return OrderTemplate(
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
