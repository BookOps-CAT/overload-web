import os

import pytest
import yaml

from overload_web.adapters import sierra_adapters


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


class TestAbstractSierraSession:
    def test_AbstractSierraSession__get_credentials(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_credentials()
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__get_target(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_target()
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__get_bibs_by_id(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_id("isbn", "9781234567890")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession_get_all_bib_ids(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session.get_all_bib_ids("isbn", "9781234567890")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession_get_bibs_by_id(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session.get_bibs_by_id("isbn", "9781234567890")
        assert str(exc.value) == "Subclasses should implement this method."


@pytest.mark.livetest
@pytest.mark.usefixtures("live_creds")
class TestLiveSierraSession:
    def test_BPLSolrSession_get_all_bib_ids(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib_ids = session.get_all_bib_ids("isbn", "9780316230032")
            assert matched_bib_ids == ["12187266"]

    def test_BPLSolrSession_get_bibs_by_id(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bibs = session.get_bibs_by_id("isbn", "9780316230032")
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 1
            assert isinstance(matched_bibs[0], dict)
            assert sorted(list(matched_bibs[0].keys())) == [
                "author_raw",
                "call_number",
                "created_date",
                "id",
                "isbn",
                "language",
                "material_type",
                "publishYear",
                "title",
            ]
            assert matched_bibs[0]["id"] == "12187266"

    def test_NYPLPlatformSession_get_all_bib_ids(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib_ids = session.get_all_bib_ids("isbn", "9780316230032")
            assert sorted(matched_bib_ids) == sorted(["21730445", "21790265"])

    def test_NYPLPlatformSession_get_bibs_by_id(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bibs = session.get_bibs_by_id("isbn", "9780316230032")
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 2
            assert isinstance(matched_bibs[0], dict)
            assert sorted(list(matched_bibs[0].keys())) == [
                "author",
                "bibLevel",
                "catalogDate",
                "controlNumber",
                "country",
                "createdDate",
                "deleted",
                "deletedDate",
                "fixedFields",
                "id",
                "lang",
                "locations",
                "materialType",
                "normAuthor",
                "normTitle",
                "nyplSource",
                "nyplType",
                "publishYear",
                "standardNumbers",
                "suppressed",
                "title",
                "updatedDate",
                "varFields",
            ]
            assert matched_bibs[0]["id"] == "21730445"
            assert matched_bibs[1]["id"] == "21790265"


@pytest.mark.usefixtures("mock_sierra_session")
class TestMockSierraSession:
    @pytest.mark.parametrize("library", ["bpl"])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_all_bib_ids(self, matchpoint):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_all_bib_ids(f"{matchpoint}", "123456789")
            assert matched_bib == ["123456789"]

    @pytest.mark.parametrize("library", ["bpl"])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bibs_by_id(self, matchpoint):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == [{"id": "123456789"}]

    @pytest.mark.parametrize("library", [None])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_all_bib_ids_no_match(self, matchpoint):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_all_bib_ids(f"{matchpoint}", "123456789")
            assert matched_bib == []

    @pytest.mark.parametrize("library", [None])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bibs_by_id_no_match(self, matchpoint):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == []

    @pytest.mark.parametrize("library", [None])
    def test_BPLSolrSession_get_all_bib_ids_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with sierra_adapters.BPLSolrSession() as session:
                session.get_all_bib_ids("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

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
    def test_NYPLPlatformSession_get_all_bib_ids(self, matchpoint):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_all_bib_ids(f"{matchpoint}", "123456789")
            assert matched_bib == ["123456789"]

    @pytest.mark.parametrize("library", ["nypl"])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bibs_by_id(self, matchpoint):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == [{"id": "123456789"}]

    @pytest.mark.parametrize("library", [None])
    def test_NYPLPlatformSession_get_all_bib_ids_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with sierra_adapters.NYPLPlatformSession() as session:
                session.get_all_bib_ids("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

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
    def test_NYPLPlatformSession_get_all_bib_ids_no_match(self, matchpoint):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_all_bib_ids(f"{matchpoint}", "123456789")
            assert matched_bib == []

    @pytest.mark.parametrize("library", [None])
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bibs_by_id_no_match(self, matchpoint):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == []
