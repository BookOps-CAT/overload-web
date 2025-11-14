import pytest

from overload_web.bib_records.infrastructure import sierra


class TestSierraBibFetcher:
    def test_fetcher_with_session(self, mock_session):
        fetcher = sierra.SierraBibFetcher(library="library", session=mock_session)
        assert isinstance(fetcher.session, sierra.SierraSessionProtocol)

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_fetcher_no_session(self, library, mock_sierra_response):
        fetcher = sierra.SierraBibFetcher(library=library)
        assert isinstance(fetcher.session, sierra.SierraSessionProtocol)

    def test_fetcher_no_session_invalid_library(self):
        with pytest.raises(ValueError) as exc:
            sierra.SierraBibFetcher(library="library")
        assert str(exc.value) == "Invalid library. Must be 'bpl' or 'nypl'"

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id(self, match, mock_session):
        fetcher = sierra.SierraBibFetcher(library="library", session=mock_session)
        bibs = fetcher.get_bibs_by_id(value="123456789", key=match)
        assert bibs[0]["bib_id"] == "123456789"

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id_no_value_passed(self, match, mock_session):
        fetcher = sierra.SierraBibFetcher(library="library", session=mock_session)
        bibs = fetcher.get_bibs_by_id(value=None, key=match)
        assert bibs == []

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_session):
        fetcher = sierra.SierraBibFetcher(library="library", session=mock_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint: 'bar'. Available matchpoints are: ['bib_id', 'isbn', 'issn', 'oclc_number', 'upc']"
        )

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id_no_response(self, match, mock_session_no_response):
        fetcher = sierra.SierraBibFetcher(
            library="library", session=mock_session_no_response
        )
        bibs = fetcher.get_bibs_by_id(value="123456789", key=match)
        assert bibs == []
