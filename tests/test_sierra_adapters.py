import pytest
from overload_web.sierra_adapters import (
    BPLSolrSession,
    NYPLPlatformSession,
    AbstractSierraSession,
)


def test_AbstractSierraSession():
    AbstractSierraSession.__abstractmethods__ = set()
    session = AbstractSierraSession()
    assert session.__dict__ == {}
    assert session._get_credentials() is None
    assert session._get_target() is None
    assert session._search_by_id("isbn", "9781234567890") is None
    assert session.get_all_bib_ids("isbn", "9781234567890") is None
    assert session.get_bib_id("isbn", "9781234567890") is None


@pytest.mark.livetest
@pytest.mark.usefixtures("live_creds")
class TestLiveSierraSession:
    def test_BPLSolrSession_get_bib_id(self, stub_bpl_order):
        with BPLSolrSession() as session:
            matched_bib = session.get_bib_id("isbn", stub_bpl_order.isbn)
            assert matched_bib == "12187266"

    def test_BPLSolrSession_get_all_bib_ids(self, stub_bpl_order):
        with BPLSolrSession() as session:
            matched_bib = session.get_all_bib_ids("isbn", stub_bpl_order.isbn)
            assert matched_bib == ["12187266"]

    def test_NYPLPlatformSession_get_bib_id(self, stub_nypl_order, live_token):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_bib_id("isbn", stub_nypl_order.isbn)
            assert matched_bib == "21730445"

    def test_NYPLPlatformSession_get_all_bib_ids(self, stub_nypl_order, live_token):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_all_bib_ids("isbn", stub_nypl_order.isbn)
            assert matched_bib == ["21730445"]


@pytest.mark.usefixtures("mock_sierra_session_response", "mock_platform_token")
class TestMockSierraSession:
    @pytest.mark.sierra_session("bpl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_all_bib_ids(self, matchpoint, stub_bpl_order):
        with BPLSolrSession() as session:
            matched_bib = session.get_all_bib_ids(
                f"{matchpoint}", getattr(stub_bpl_order, f"{matchpoint}")
            )
            assert matched_bib == ["123456789"]

    @pytest.mark.sierra_session("bpl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_all_bib_ids_no_match(self, matchpoint, stub_bpl_order):
        with BPLSolrSession() as session:
            matched_bib = session.get_all_bib_ids(
                f"{matchpoint}", getattr(stub_bpl_order, f"{matchpoint}")
            )
            assert matched_bib is None

    @pytest.mark.sierra_session("bpl_404")
    def test_BPLSolrSession_get_all_bib_ids_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with BPLSolrSession() as session:
                session.get_all_bib_ids("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("bpl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bib_id(self, matchpoint, stub_bpl_order):
        with BPLSolrSession() as session:
            matched_bib = session.get_bib_id(
                f"{matchpoint}", getattr(stub_bpl_order, f"{matchpoint}")
            )
            assert matched_bib == "123456789"

    @pytest.mark.sierra_session("bpl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bib_id_no_match(self, matchpoint, stub_bpl_order):
        with BPLSolrSession() as session:
            matched_bib = session.get_bib_id(
                f"{matchpoint}", getattr(stub_bpl_order, f"{matchpoint}")
            )
            assert matched_bib is None

    @pytest.mark.sierra_session("bpl_404")
    def test_BPLSolrSession_get_bib_id_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with BPLSolrSession() as session:
                session.get_bib_id("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_all_bib_ids(self, matchpoint, stub_nypl_order):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_all_bib_ids(
                f"{matchpoint}", getattr(stub_nypl_order, f"{matchpoint}")
            )
            assert matched_bib == ["123456789"]

    @pytest.mark.sierra_session("nypl_404")
    def test_NYPLPlatformSession_get_all_bib_ids_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with NYPLPlatformSession() as session:
                session.get_all_bib_ids("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_all_bib_ids_no_match(
        self, matchpoint, stub_nypl_order
    ):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_all_bib_ids(
                f"{matchpoint}", getattr(stub_nypl_order, f"{matchpoint}")
            )
            assert matched_bib is None

    @pytest.mark.sierra_session("nypl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bib_id(self, matchpoint, stub_nypl_order):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_bib_id(
                f"{matchpoint}", getattr(stub_nypl_order, f"{matchpoint}")
            )
            assert matched_bib == "123456789"

    @pytest.mark.sierra_session("nypl_404")
    def test_NYPLSolrSession_get_bib_id_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with NYPLPlatformSession() as session:
                session.get_bib_id("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bib_id_no_match(self, matchpoint, stub_nypl_order):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_bib_id(
                f"{matchpoint}", getattr(stub_nypl_order, f"{matchpoint}")
            )
            assert matched_bib is None
