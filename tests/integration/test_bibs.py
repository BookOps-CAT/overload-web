import pytest

from overload_web.infrastructure.bibs import sierra


@pytest.mark.parametrize("library", ["bpl", "nypl"])
@pytest.mark.usefixtures("mock_sierra_response")
class TestSierraBibFetcher:
    def test_fetcher(self, library):
        session = sierra.SierraBibFetcher(library=library)
        assert isinstance(session.session, sierra.SierraSessionProtocol)

    def test_fetcher_invalid_library(self, library):
        with pytest.raises(ValueError) as exc:
            sierra.SierraBibFetcher(library="library")
        assert str(exc.value) == "Invalid library. Must be 'bpl' or 'nypl'"

    @pytest.mark.parametrize("matchpoint", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_by_id(self, library, matchpoint):
        session = sierra.SierraBibFetcher(library=library)
        bibs = session.get_bibs_by_id(value="123456789", key=matchpoint)
        assert bibs[0]["bib_id"] == "123456789"

    def test_get_bibs_by_issn(self, library):
        session = sierra.SierraBibFetcher(library=library)
        with pytest.raises(NotImplementedError) as exc:
            session.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented" in str(exc.value)

    @pytest.mark.parametrize("matchpoint", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_by_id_no_value_passed(self, library, matchpoint):
        session = sierra.SierraBibFetcher(library=library)
        bibs = session.get_bibs_by_id(value=None, key=matchpoint)
        assert bibs == []

    def test_get_bibs_by_id_invalid_matchpoint(self, library):
        session = sierra.SierraBibFetcher(library=library)
        with pytest.raises(ValueError) as exc:
            session.get_bibs_by_id(value="123456789", key="bar")
        assert (
            str(exc.value)
            == "Invalid matchpoint: 'bar'. Available matchpoints are: ['bib_id', 'isbn', 'issn', 'oclc_number', 'upc']"
        )
