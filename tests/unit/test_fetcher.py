import pytest

from overload_web.infrastructure import clients


class TestSierraBibFetcher:
    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id(self, match, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        bibs = fetcher.get_bibs_by_id(value="123456789", key=match)
        assert bibs[0].bib_id == "123456789"
        assert isinstance(fetcher.session, clients.SierraSessionProtocol)
        assert "Querying Sierra " in caplog.text

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert "Unsupported query matchpoint: 'bar'" in caplog.text
        assert "Invalid matchpoint: 'bar'. Available matchpoints are:" in str(exc.value)

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id_no_value_passed(self, match, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        bibs = fetcher.get_bibs_by_id(value=None, key=match)
        assert bibs == []
        assert f"Skipping Sierra query on {match} with missing value." in caplog.text

    def test_get_bibs_by_id_nypl_error(self, mock_nypl_session_error, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_nypl_session_error)
        with pytest.raises(clients.BookopsPlatformError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsPlatformError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_bpl_error(self, mock_bpl_session_error, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_bpl_session_error)
        with pytest.raises(clients.BookopsSolrError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsSolrError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_nypl_issn(self, mock_session):
        fetcher = clients.SierraBibFetcher(session=clients.NYPLPlatformSession())
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in NYPL Platform" in str(exc.value)

    def test_get_bibs_by_id_bpl_issn(self, mock_session):
        fetcher = clients.SierraBibFetcher(session=clients.BPLSolrSession())
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in BPL Solr" in str(exc.value)


class TestFetcherFactory:
    @pytest.mark.parametrize(
        "library,session_type",
        [("bpl", "BPLSolrSession"), ("nypl", "NYPLPlatformSession")],
    )
    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_fetcher_factory(self, library, session_type, mock_session, match, caplog):
        fetcher = clients.FetcherFactory().make(library=library)
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert f"Querying Sierra with {session_type}" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == session_type

    def test_fetcher_factory_nypl_auth_error(self, mock_nypl_session_error):
        with pytest.raises(clients.BookopsPlatformError) as exc:
            clients.FetcherFactory().make(library="nypl")
        assert "Trouble connecting: " in str(exc.value)

    def test_fetcher_factory_invalid_library(self):
        with pytest.raises(ValueError) as exc:
            clients.FetcherFactory().make(library="library")
        assert str(exc.value) == "Invalid library: library. Must be 'bpl' or 'nypl'"
