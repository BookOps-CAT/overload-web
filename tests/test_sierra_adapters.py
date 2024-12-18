import os
import pytest
from overload_web.sierra_adapters import (
    BPLSolrSession,
    NYPLPlatformSession,
    AbstractSierraSession,
)


def test_AbstractSierraSession(stub_bpl_order):
    AbstractSierraSession.__abstractmethods__ = set()
    session = AbstractSierraSession()
    assert session.__dict__ == {}
    assert session.match_order(stub_bpl_order, ["isbn"]) is None
    assert session._match_order(stub_bpl_order, ["isbn"]) is None


@pytest.mark.usefixtures("live_creds")
class TestLiveSierraSession:
    def test_BPLSolrSession(self, stub_bpl_order):
        with BPLSolrSession(
            authorization=os.environ["BPL_SOLR_CLIENT_KEY"],
            endpoint=os.environ["BPL_SOLR_ENDPOINT"],
        ) as session:
            matched_bib = session.match_order(
                order=stub_bpl_order, matchpoints=["isbn"]
            )
            assert matched_bib == ["12187266"]

    def test_NYPLPlatformSession_live(self, stub_nypl_order, live_token):
        with NYPLPlatformSession(
            authorization=live_token,
            target=os.environ["NYPL_PLATFORM_TARGET"],
        ) as session:
            matched_bib = session.match_order(
                order=stub_nypl_order, matchpoints=["isbn"]
            )
            assert matched_bib == ["21730445"]


@pytest.mark.usefixtures("mock_sierra_session_response")
class TestMockSierraSession:
    @pytest.mark.sierra_session("bpl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_match(self, matchpoint, stub_bpl_order):
        with BPLSolrSession(
            authorization="my_key",
            endpoint="my_endpoint",
        ) as session:
            matched_bib = session.match_order(
                order=stub_bpl_order, matchpoints=[f"{matchpoint}"]
            )
            assert matched_bib == ["123456789"]

    @pytest.mark.sierra_session("bpl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_BPLSolrSession_no_match(self, matchpoint, stub_bpl_order):
        with BPLSolrSession(
            authorization="my_key",
            endpoint="my_endpoint",
        ) as session:
            matched_bib = session.match_order(
                order=stub_bpl_order, matchpoints=[f"{matchpoint}"]
            )
            assert matched_bib is None

    @pytest.mark.sierra_session("bpl_404")
    def test_BPLSolrSession_match_invalid_matchpoint(self, stub_bpl_order):
        with pytest.raises(ValueError) as exc:
            with BPLSolrSession(
                authorization="my_key",
                endpoint="my_endpoint",
            ) as session:
                session.match_order(order=stub_bpl_order, matchpoints=["foo"])
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_ok")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_match(
        self, matchpoint, stub_nypl_order, mock_platform_token
    ):
        with NYPLPlatformSession(
            authorization=mock_platform_token,
            target="dev",
        ) as session:
            matched_bib = session.match_order(
                order=stub_nypl_order, matchpoints=[f"{matchpoint}"]
            )
            assert matched_bib == ["123456789"]

    @pytest.mark.sierra_session("nypl_404")
    def test_NYPLSolrSession_match_invalid_matchpoint(
        self, stub_nypl_order, mock_platform_token
    ):
        with pytest.raises(ValueError) as exc:
            with NYPLPlatformSession(
                authorization=mock_platform_token,
                target="dev",
            ) as session:
                session.match_order(order=stub_nypl_order, matchpoints=["foo"])
        assert (
            str(exc.value)
            == "Invalid matchpoint. Available matchpoints are: bib_id, oclc_number, isbn, and upc"
        )

    @pytest.mark.sierra_session("nypl_404")
    @pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
    def test_NYPLPlatformSession_no_match(
        self, matchpoint, stub_nypl_order, mock_platform_token
    ):
        with NYPLPlatformSession(
            authorization=mock_platform_token,
            target="dev",
        ) as session:
            matched_bib = session.match_order(
                order=stub_nypl_order, matchpoints=[f"{matchpoint}"]
            )
            assert matched_bib is None
