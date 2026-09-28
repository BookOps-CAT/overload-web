from contextlib import nullcontext as does_not_raise

import pytest

from overload_web.infrastructure import sierra_clients


class TestSierraBibFetcher:
    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "control_number"])
    def test_get_bibs_by_id_bpl(self, mock_sierra_session, match, caplog):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert "Querying Sierra with BPLSolrSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "BPLSolrSession"

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "control_number"])
    def test_get_bibs_by_id_nypl(self, mock_sierra_session, match, caplog):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert "Querying Sierra with NYPLPlatformSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "NYPLPlatformSession"

    def test_get_bibs_by_id_bpl_issn(self, mock_sierra_session):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in BPL Solr" in str(exc.value)

    def test_get_bibs_by_id_nypl_issn(self, mock_sierra_session):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in NYPL Platform" in str(exc.value)

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_sierra_session, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert "Unsupported query matchpoint: 'bar'" in caplog.text
        assert "Invalid matchpoint: 'bar'. Available matchpoints are:" in str(exc.value)

    @pytest.mark.parametrize(
        "match", ["bib_id", "upc", "isbn", "control_number", "issn"]
    )
    def test_get_bibs_by_id_no_value_passed(self, match, mock_sierra_session, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        bibs = fetcher.get_bibs_by_id(value=None, key=match)
        assert bibs == []
        assert f"Skipping Sierra query on {match} with missing value." in caplog.text

    @pytest.mark.parametrize("id", [".b123", ".i123", ".o123", "123", 123, 123456789])
    def test__prep_sierra_number_bpl_override(self, mock_sierra_session, id):
        """Test `_prep_sierra_number override."""
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    @pytest.mark.parametrize("id", [".b123", ".i123", ".o123", "123", 123, 123456789])
    def test__prep_sierra_number_nypl_override(self, mock_sierra_session, id):
        """Test `_prep_sierra_number override."""
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    def test_get_bibs_by_id_bpl_error(self, mock_bpl_session_error, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_bpl_session_error)
        with pytest.raises(sierra_clients.BookopsSolrError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsSolrError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_nypl_error(self, mock_nypl_session_error, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_nypl_session_error)
        with pytest.raises(sierra_clients.BookopsPlatformError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsPlatformError while running Sierra queries." in caplog.text

    @pytest.mark.parametrize(
        "library, session_type",
        [("nypl", "NYPLPlatformSession"), ("bpl", "BPLSolrSession")],
    )
    def test_fetcher_factory(self, mock_sierra_session, library, session_type):
        fetcher = sierra_clients.FetcherFactory.make(library=library)
        assert isinstance(fetcher, sierra_clients.SierraBibFetcher)
        assert fetcher.session.__class__.__name__ == session_type

    def test_fetcher_factory_invalid_library(self, mock_sierra_session):
        with pytest.raises(ValueError) as exc:
            sierra_clients.FetcherFactory.make(library="foo")
        assert str(exc.value) == "Invalid library: foo. Must be 'bpl' or 'nypl'"

    def test_fetcher_factory_platform_error(self, mock_nypl_session_error):
        with pytest.raises(sierra_clients.BookopsPlatformError) as exc:
            sierra_clients.FetcherFactory.make(library="nypl")
        assert "Trouble connecting: " in str(exc.value)
