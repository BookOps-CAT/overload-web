import datetime
import io
import os

import pytest
import yaml

from overload_web.adapters import marc_adapters, sierra_adapters


class MockHTTPResponse:
    def __init__(self, status_code: int, ok: bool, stub_json: dict):
        self.status_code = status_code
        self.ok = ok
        self.stub_json = stub_json

    def json(self):
        return self.stub_json


@pytest.fixture
def live_creds() -> None:
    with open(
        os.path.join(os.environ["USERPROFILE"], ".cred/.overload/live_creds.yaml")
    ) as cred_file:
        data = yaml.safe_load(cred_file)
        for k, v in data.items():
            os.environ[k] = v


@pytest.fixture
def mock_sierra_session(library, monkeypatch):
    if library == "nypl":
        code, ok, json = 200, True, {"data": [{"id": "123456789"}]}
    elif library == "bpl":
        code, ok, json = 200, True, {"response": {"docs": [{"id": "123456789"}]}}
    else:
        code, ok, json = 404, False, {}

    def mock_api_response(*args, code=code, ok=ok, json=json, **kwargs):
        return MockHTTPResponse(status_code=code, ok=ok, stub_json=json)

    def mock_token_response(*args, **kwargs):
        token_json = {"access_token": "foo", "expires_in": 10}
        return MockHTTPResponse(status_code=200, ok=True, stub_json=token_json)

    monkeypatch.setattr("requests.post", mock_token_response)
    monkeypatch.setattr("requests.Session.get", mock_api_response)
    monkeypatch.setenv("NYPL_PLATFORM_CLIENT", "test")
    monkeypatch.setenv("NYPL_PLATFORM_SECRET", "test")
    monkeypatch.setenv("NYPL_PLATFORM_OAUTH", "test")
    monkeypatch.setenv("NYPL_PLATFORM_AGENT", "test")
    monkeypatch.setenv("NYPL_PLATFORM_TARGET", "dev")
    monkeypatch.setenv("BPL_SOLR_CLIENT", "test")
    monkeypatch.setenv("BPL_SOLR_TARGET", "dev")


def test_AbstractSierraSession():
    sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
    session = sierra_adapters.AbstractSierraSession()
    assert session.__dict__ == {}
    assert session._get_credentials() is None
    assert session._get_target() is None
    assert session._get_bibs_by_id("isbn", "9781234567890") is None
    assert session.get_bibs_by_id("isbn", "9781234567890") is None


@pytest.mark.livetest
@pytest.mark.usefixtures("live_creds")
class TestLiveSierraSession:
    def test_BPLSolrSession_get_bibs_by_id(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id("isbn", "9780316230032")
            assert matched_bib == ["12187266"]

    def test_NYPLPlatformSession_get_bibs_by_id(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id("isbn", "9780316230032")
            assert sorted(matched_bib) == sorted(["21730445", "21790265"])


@pytest.mark.usefixtures("mock_sierra_session")
class TestMockSierraSession:
    @pytest.mark.parametrize("library", ["bpl"])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bibs_by_id(self, matchpoint):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == ["123456789"]

    @pytest.mark.parametrize("library", [None])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bibs_by_id_no_match(self, matchpoint):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == []

    @pytest.mark.parametrize("library", [None])
    def test_BPLSolrSession_get_bibs_by_id_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with sierra_adapters.BPLSolrSession() as session:
                session.get_bibs_by_id("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.parametrize("library", ["nypl"])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bibs_by_id(self, matchpoint):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == ["123456789"]

    @pytest.mark.parametrize("library", [None])
    def test_NYPLPlatformSession_get_bibs_by_id_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with sierra_adapters.NYPLPlatformSession() as session:
                session.get_bibs_by_id("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.parametrize("library", [None])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bibs_by_id_no_match(self, matchpoint):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == []


class TestOverloadBib:
    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OverloadBib(self, stub_bib, library):
        bib = marc_adapters.OverloadBib()
        bib.leader = stub_bib.leader
        bib.fields = stub_bib.fields
        bib.library = stub_bib.library
        assert hasattr(bib, "isbn")
        assert hasattr(bib, "sierra_bib_id")
        assert hasattr(bib, "orders")
        assert isinstance(bib, marc_adapters.OverloadBib)
        assert isinstance(bib.orders, list)
        assert isinstance(bib.orders[0], marc_adapters.OverloadOrder)
        assert bib.orders[0].audience == "a"
        assert bib.orders[0].blanket_po == "baz"
        assert bib.orders[0].copies == 13
        assert bib.orders[0].country == "xxu"
        assert bib.orders[0].created == datetime.date(2025, 1, 1)
        assert bib.orders[0].form == "b"
        assert bib.orders[0].fund == "lease"
        assert bib.orders[0].internal_note == "foo"
        assert bib.orders[0].lang == "eng"
        assert bib.orders[0].locs == ["agj0y"]
        assert bib.orders[0].order_type == "l"
        assert bib.orders[0].price == "{{dollar}}13.20"
        assert bib.orders[0].selector == "j"
        assert bib.orders[0].source == "d"
        assert bib.orders[0].status == "o"
        assert bib.orders[0].var_field_isbn == "bar"
        assert bib.orders[0].vendor_code == "btlea"
        assert bib.orders[0].venNotes == "baz"
        assert bib.orders[0].vendor_title_no == "foo"

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OverloadBib_no_following_field(self, stub_bib, library):
        assert stub_bib.orders[0].venNotes == "baz"
        stub_bib.remove_fields("961")
        bib = marc_adapters.OverloadBib.from_bookops_bib(stub_bib)
        assert isinstance(bib.orders, list)
        assert isinstance(bib.orders[0], marc_adapters.OverloadOrder)
        assert bib.orders[0].audience == "a"
        assert bib.orders[0].blanket_po is None
        assert bib.orders[0].copies == 13
        assert bib.orders[0].country == "xxu"
        assert bib.orders[0].created == datetime.date(2025, 1, 1)
        assert bib.orders[0].form == "b"
        assert bib.orders[0].fund == "lease"
        assert bib.orders[0].internal_note is None
        assert bib.orders[0].lang == "eng"
        assert bib.orders[0].locs == ["agj0y"]
        assert bib.orders[0].order_type == "l"
        assert bib.orders[0].price == "{{dollar}}13.20"
        assert bib.orders[0].selector == "j"
        assert bib.orders[0].selector_note is None
        assert bib.orders[0].source == "d"
        assert bib.orders[0].status == "o"
        assert bib.orders[0].var_field_isbn is None
        assert bib.orders[0].vendor_code == "btlea"
        assert bib.orders[0].venNotes is None
        assert bib.orders[0].vendor_title_no is None

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OverloadBib_from_bookops_bib(self, stub_bib, library):
        bib = marc_adapters.OverloadBib.from_bookops_bib(stub_bib)
        assert hasattr(bib, "isbn")
        assert hasattr(bib, "sierra_bib_id")
        assert hasattr(bib, "orders")
        assert isinstance(bib, marc_adapters.OverloadBib)
        assert isinstance(stub_bib, marc_adapters.Bib)
        assert isinstance(bib.orders, list)
        assert isinstance(bib.orders[0], marc_adapters.OverloadOrder)
        assert isinstance(stub_bib.orders[0], marc_adapters.BookopsMarcOrder)
        assert bib.library == stub_bib.library
        assert bib.sierra_bib_id == stub_bib.sierra_bib_id


class TestOverloadOrder:
    def test_OverloadOrder(self, stub_960, stub_961):
        order = marc_adapters.OverloadOrder(stub_960, stub_961)
        assert order.audience == "a"
        assert order.blanket_po == "baz"
        assert order.copies == 13
        assert order.country == "xxu"
        assert order.created == datetime.date(2025, 1, 1)
        assert order.form == "b"
        assert order.fund == "lease"
        assert order.internal_note == "foo"
        assert order.lang == "eng"
        assert order.locs == ["agj0y"]
        assert order.order_type == "l"
        assert order.price == "{{dollar}}13.20"
        assert order.selector == "j"
        assert order.source == "d"
        assert order.status == "o"
        assert order.var_field_isbn == "bar"
        assert order.vendor_code == "btlea"
        assert order.venNotes == "baz"
        assert order.vendor_title_no == "foo"

    def test_OverloadOrder_no_var_fields(self, stub_960):
        order = marc_adapters.OverloadOrder(stub_960)
        assert order.audience == "a"
        assert order.blanket_po is None
        assert order.copies == 13
        assert order.country == "xxu"
        assert order.created == datetime.date(2025, 1, 1)
        assert order.form == "b"
        assert order.fund == "lease"
        assert order.internal_note is None
        assert order.lang == "eng"
        assert order.locs == ["agj0y"]
        assert order.order_type == "l"
        assert order.price == "{{dollar}}13.20"
        assert order.selector == "j"
        assert order.selector_note is None
        assert order.source == "d"
        assert order.status == "o"
        assert order.var_field_isbn is None
        assert order.vendor_code == "btlea"
        assert order.venNotes is None
        assert order.vendor_title_no is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_read_marc_file(stub_bib, library):
    bib_file = io.BytesIO(stub_bib.as_marc())
    bib_list = [i for i in marc_adapters.read_marc_file(bib_file, library)]
    assert len(bib_list) == 1
