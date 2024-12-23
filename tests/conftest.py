from datetime import datetime
import os
import yaml
import pytest

from overload_web.domain.model import (
    Order,
    FixedOrderData,
    VariableOrderData,
    OrderTemplate,
)
from overload_web.sierra_adapters import (
    PlatformToken,
    SierraService,
    AbstractSierraSession,
)


@pytest.fixture
def live_creds() -> None:
    with open(
        os.path.join(os.environ["USERPROFILE"], ".cred/.overload/test_creds.yaml")
    ) as cred_file:
        data = yaml.safe_load(cred_file)
        for k, v in data.items():
            os.environ[k] = v


@pytest.fixture
def live_token(live_creds) -> PlatformToken:
    return PlatformToken(
        os.environ["NYPL_PLATFORM_CLIENT"],
        os.environ["NYPL_PLATFORM_SECRET"],
        os.environ["NYPL_PLATFORM_OAUTH"],
        os.environ["NYPL_PLATFORM_AGENT"],
    )


class MockHTTPResponse:
    def __init__(self, status_code: int, ok: bool, stub_json: dict):
        self.status_code = status_code
        self.ok = ok
        self.stub_json = stub_json

    def json(self):
        return self.stub_json


@pytest.fixture
def mock_platform_token(monkeypatch):
    def mock_api_response(*args, **kwargs):
        token_json = {"access_token": "foo", "expires_in": 10}
        return MockHTTPResponse(status_code=200, ok=True, stub_json=token_json)

    monkeypatch.setenv("NYPL_PLATFORM_CLIENT", "app_client_id")
    monkeypatch.setenv("NYPL_PLATFORM_SECRET", "app_secret")
    monkeypatch.setenv("NYPL_PLATFORM_OAUTH", "outh_server")
    monkeypatch.setenv("NYPL_PLATFORM_AGENT", "dev")
    monkeypatch.setenv("NYPL_PLATFORM_TARGET", "dev")
    monkeypatch.setenv("BPL_SOLR_CLIENT_KEY", "solr_key")
    monkeypatch.setenv("BPL_SOLR_ENDPOINT", "solr_endpoint")
    monkeypatch.setattr("requests.post", mock_api_response)
    return PlatformToken("client-id", "client-secret", "oauth-server", "agent")


@pytest.fixture
def mock_sierra_session_response(monkeypatch, request, mock_platform_token):
    marker = request.node.get_closest_marker("sierra_session").args[0]
    if marker == "nypl_ok":
        code, ok = 200, True
        json = {"data": [{"id": "123456789"}]}
    elif marker == "bpl_ok":
        code, ok = 200, True
        json = {"response": {"docs": [{"id": "123456789"}]}}
    else:
        code, ok = 404, False
        json = {}

    def mock_api_response(*args, code=code, ok=ok, json=json, **kwargs):
        return MockHTTPResponse(status_code=code, ok=ok, stub_json=json)

    monkeypatch.setattr("requests.Session.get", mock_api_response)


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
def stub_sierra_service(mock_sierra_session_response):
    service = SierraService(MockSierraAdapter())
    return service


@pytest.fixture
def stub_bpl_order(stub_order_fixed_field, stub_order_variable_field):
    return Order(
        bib_id="123456789",
        isbn="9780316230032",
        oclc_number="(OCoLC)00012345",
        upc="123456",
        fixed_field=stub_order_fixed_field,
        library="bpl",
        variable_field=stub_order_variable_field,
    )


@pytest.fixture
def stub_nypl_order(stub_order_fixed_field, stub_order_variable_field):
    return Order(
        bib_id="123456789",
        isbn="9780316230032",
        oclc_number="(OCoLC)00012345",
        upc="123456",
        fixed_field=stub_order_fixed_field,
        library="nypl",
        variable_field=stub_order_variable_field,
    )


@pytest.fixture
def stub_order(stub_order_fixed_field, stub_order_variable_field):
    return Order(
        fixed_field=stub_order_fixed_field,
        library="nypl",
        variable_field=stub_order_variable_field,
    )


@pytest.fixture
def stub_order_fixed_field():
    return FixedOrderData(
        datetime(2024, 1, 1),
        ["(4)fwa0f", "(2)bca0f", "gka0f"],
        ["0f", "0f", "0f"],
        "$5.00",
        "25240adbk",
        "7",
        "eng",
        "xxu",
        "0049",
        "a",
        "b",
        ["a", "a", "a"],
        "d",
        "p",
        "o",
    )


@pytest.fixture
def stub_order_variable_field():
    return VariableOrderData(None, None, None, None, None)


@pytest.fixture
def stub_template():
    return OrderTemplate(
        datetime(2024, 1, 1),
        ["(2)tbca0f", "cna0f", "cia0f", "csa0f"],
        ["0f", "0f", "0f", "0f"],
        "$20.00",
        "10001adbk",
        "7",
        "spa",
        "xxu",
        "0049",
        "a",
        "b",
        ["a", "a", "a", "a"],
        "d",
        "p",
        "o",
        "foo",
        None,
        "bar",
        None,
        None,
        "isbn",
        None,
        None,
    )
