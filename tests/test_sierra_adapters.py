import os

import pytest
import yaml

from overload_web.infrastructure import sierra_adapters


@pytest.fixture
def mock_session(library, mock_sierra_response):
    if library == "bpl":
        session = sierra_adapters.BPLSolrSession()
    else:
        session = sierra_adapters.NYPLPlatformSession()
    return session


@pytest.fixture
def live_creds() -> None:
    with open(
        os.path.join(os.environ["USERPROFILE"], ".cred/.overload/live_creds.yaml")
    ) as cred_file:
        data = yaml.safe_load(cred_file)
        for k, v in data.items():
            os.environ[k] = v


class TestAbstractObjects:
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

    def test_AbstractSierraSession__get_bibs_by_bib_id(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_bib_id("12345")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__get_bibs_by_isbn(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_isbn("12345")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__get_bibs_by_issn(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_issn("12345")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__get_bibs_by_oclc_number(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_oclc_number("12345")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__get_bibs_by_upc(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_upc("12345")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractSierraSession__parse_response(self):
        sierra_adapters.AbstractSierraSession.__abstractmethods__ = set()
        session = sierra_adapters.AbstractSierraSession()
        with pytest.raises(NotImplementedError) as exc:
            session._parse_response("foo")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractService__get_bibs_by_id(self):
        sierra_adapters.AbstractService.__abstractmethods__ = set()
        session = sierra_adapters.AbstractService()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_id("foo", "isbn")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_AbstractService_get_bibs_by_id(self):
        sierra_adapters.AbstractService.__abstractmethods__ = set()
        session = sierra_adapters.AbstractService()
        with pytest.raises(NotImplementedError) as exc:
            session._get_bibs_by_id("foo", "isbn")
        assert str(exc.value) == "Subclasses should implement this method."


@pytest.mark.livetest
@pytest.mark.usefixtures("live_creds")
class TestLiveSierraSession:
    def test_BPLSolrSession_live(self):
        with sierra_adapters.BPLSolrSession() as session:
            response = session._get_bibs_by_isbn("9780316230032")
            matched_bibs = session._parse_response(response=response)
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

    def test_NYPLPlatformSession_live(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            response = session._get_bibs_by_isbn("9780316230032")
            matched_bibs = session._parse_response(response=response)
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


@pytest.mark.usefixtures("mock_sierra_response")
class TestMockSierraSession:
    def test_BPLSolrSession__get_bibs_by_bib_id(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session._get_bibs_by_bib_id("123456789")
            assert matched_bib.json() == {"response": {"docs": [{"id": "123456789"}]}}

    def test_BPLSolrSession__get_bibs_by_isbn(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session._get_bibs_by_isbn("123456789")
            assert matched_bib.json() == {"response": {"docs": [{"id": "123456789"}]}}

    def test_BPLSolrSession__get_bibs_by_issn(self):
        with sierra_adapters.BPLSolrSession() as session:
            with pytest.raises(NotImplementedError) as exc:
                session._get_bibs_by_issn("foo")
            assert str(exc.value) == "Search by ISSN not implemented in BPL Solr"

    def test_BPLSolrSession__get_bibs_by_oclc_number(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session._get_bibs_by_oclc_number("123456789")
            assert matched_bib.json() == {"response": {"docs": [{"id": "123456789"}]}}

    def test_BPLSolrSession__get_bibs_by_upc(self):
        with sierra_adapters.BPLSolrSession() as session:
            matched_bib = session._get_bibs_by_upc("123456789")
            assert matched_bib.json() == {"response": {"docs": [{"id": "123456789"}]}}

    def test_NYPLPlatformSession__get_bibs_by_bib_id(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session._get_bibs_by_bib_id("123456789")
            assert matched_bib.json() == {"data": [{"id": "123456789"}]}

    def test_NYPLPlatformSession__get_bibs_by_isbn(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session._get_bibs_by_isbn("123456789")
            assert matched_bib.json() == {"data": [{"id": "123456789"}]}

    def test_NYPLPlatformSession__get_bibs_by_issn(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            with pytest.raises(NotImplementedError) as exc:
                session._get_bibs_by_issn("foo")
            assert str(exc.value) == "Search by ISSN not implemented in NYPL Platform"

    def test_NYPLPlatformSession__get_bibs_by_oclc_number(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session._get_bibs_by_oclc_number("123456789")
            assert matched_bib.json() == {"data": [{"id": "123456789"}]}

    def test_NYPLPlatformSession__get_bibs_by_upc(self):
        with sierra_adapters.NYPLPlatformSession() as session:
            matched_bib = session._get_bibs_by_upc("123456789")
            assert matched_bib.json() == {"data": [{"id": "123456789"}]}


@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestSierraService:
    @pytest.mark.parametrize("matchpoint", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_by_id(self, library, matchpoint, mock_session):
        session = sierra_adapters.SierraService(session=mock_session)
        bibs = session.get_bibs_by_id(value="123456789", key=matchpoint)
        assert bibs == [{"id": "123456789"}]

    def test_get_bibs_by_issn(self, library, mock_session):
        session = sierra_adapters.SierraService(session=mock_session)
        with pytest.raises(NotImplementedError) as exc:
            session.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented" in str(exc.value)

    @pytest.mark.parametrize("matchpoint", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_no_value(self, library, matchpoint, mock_session):
        session = sierra_adapters.SierraService(session=mock_session)
        bibs = session.get_bibs_by_id(value=None, key=matchpoint)
        assert bibs == []

    def test_get_bibs_by_id_invalid_matchpoint(self, library, mock_session):
        session = sierra_adapters.SierraService(session=mock_session)
        with pytest.raises(ValueError) as exc:
            session.get_bibs_by_id(value="123456789", key="bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, issn, and upc"
        )
