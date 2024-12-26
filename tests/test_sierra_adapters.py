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
    assert session._get_bibs_by_id("isbn", "9781234567890") is None
    assert session.get_bibs_by_id("isbn", "9781234567890") is None


@pytest.mark.livetest
@pytest.mark.usefixtures("live_creds", "live_token")
class TestLiveSierraSession:
    def test_BPLSolrSession_get_bibs_by_id(self):
        with BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id("isbn", "9780316230032")
            assert matched_bib == ["12187266"]

    def test_NYPLPlatformSession_get_bibs_by_id(self):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id("isbn", "9780316230032")
            assert matched_bib == ["21730445"]


@pytest.mark.usefixtures("mock_sierra_session_response")
class TestMockSierraSession:
    @pytest.mark.sierra_session("bpl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bibs_by_id(self, matchpoint):
        with BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == ["123456789"]

    @pytest.mark.sierra_session("bpl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_get_bibs_by_id_no_match(self, matchpoint):
        with BPLSolrSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == []

    @pytest.mark.sierra_session("bpl_404")
    def test_BPLSolrSession_get_bibs_by_id_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with BPLSolrSession() as session:
                session.get_bibs_by_id("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bibs_by_id(self, matchpoint):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == ["123456789"]

    @pytest.mark.sierra_session("nypl_404")
    def test_NYPLPlatformSession_get_bibs_by_id_invalid_matchpoint(self):
        with pytest.raises(ValueError) as exc:
            with NYPLPlatformSession() as session:
                session.get_bibs_by_id("foo", "bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_get_bibs_by_id_no_match(self, matchpoint):
        with NYPLPlatformSession() as session:
            matched_bib = session.get_bibs_by_id(f"{matchpoint}", "123456789")
            assert matched_bib == []
