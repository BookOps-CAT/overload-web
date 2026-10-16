from contextlib import nullcontext as does_not_raise

import pytest
from requests.exceptions import Timeout

from overload_web.infrastructure import sierra_clients


class TestSierraBibFetcher:
    @pytest.mark.parametrize(
        "key,expectation",
        [
            ("bib_id", does_not_raise()),
            ("upc", does_not_raise()),
            ("isbn", does_not_raise()),
            ("control_number", does_not_raise()),
            ("issn", pytest.raises(NotImplementedError)),
        ],
    )
    def test_get_bibs_by_id_bpl(self, mock_sierra_session, key, expectation, caplog):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        with expectation:
            fetcher.get_bibs_by_id(value="123456789", key=key)
        assert "Querying Sierra with BPLSolrSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "BPLSolrSession"

    @pytest.mark.parametrize(
        "key,expectation",
        [
            ("bib_id", does_not_raise()),
            ("upc", does_not_raise()),
            ("isbn", does_not_raise()),
            ("control_number", does_not_raise()),
            ("issn", pytest.raises(NotImplementedError)),
        ],
    )
    def test_get_bibs_by_id_nypl(self, mock_sierra_session, key, expectation, caplog):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        with expectation:
            fetcher.get_bibs_by_id(value="123456789", key=key)
        assert "Querying Sierra with NYPLPlatformSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "NYPLPlatformSession"

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_sierra_session, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert "Unsupported query matchpoint: 'bar'" in caplog.text
        assert "Invalid matchpoint: 'bar'. Available matchpoints are:" in str(exc.value)

    def test_get_bibs_by_id_no_value_passed(self, mock_sierra_session, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        bibs = fetcher.get_bibs_by_id(value=None, key="isbn")
        assert bibs == []
        assert "Skipping Sierra query on isbn with missing value." in caplog.text

    @pytest.mark.parametrize("id", [".b123", "123", 123456789])
    def test__prep_sierra_number_bpl_override(self, mock_sierra_session, id):
        """Test `_prep_sierra_number override."""
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    @pytest.mark.parametrize("id", [".b123", "123", 123456789])
    def test__prep_sierra_number_nypl_override(self, mock_sierra_session, id):
        """Test `_prep_sierra_number override."""
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    def test_get_bibs_by_id_bpl_error(self, mock_sierra_session, mocker, caplog):
        mock = mocker.Mock(side_effect=sierra_clients.BookopsSolrError)
        mocker.patch.object(mock_sierra_session, "_get_bibs_by_isbn", mock)
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        with pytest.raises(sierra_clients.BookopsSolrError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsSolrError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_nypl_error(self, mock_sierra_session, mocker, caplog):
        mock = mocker.Mock(side_effect=sierra_clients.BookopsPlatformError)
        mocker.patch.object(mock_sierra_session, "_get_bibs_by_isbn", mock)
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        with pytest.raises(sierra_clients.BookopsPlatformError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsPlatformError while running Sierra queries." in caplog.text

    @pytest.mark.parametrize(
        "library,expectation",
        [
            ("nypl", does_not_raise()),
            ("bpl", does_not_raise()),
            ("foo", pytest.raises(ValueError)),
        ],
    )
    def test_fetcher_factory(self, mock_sierra_session, library, expectation):
        with expectation:
            sierra_clients.FetcherFactory.make(library=library)

    def test_fetcher_factory_platform_error(self, mocker):
        mock = mocker.Mock(side_effect=Timeout)
        mocker.patch("requests.post", mock)
        with pytest.raises(sierra_clients.BookopsPlatformError) as exc:
            sierra_clients.FetcherFactory.make(library="nypl")
        assert "Trouble connecting: " in str(exc.value)
