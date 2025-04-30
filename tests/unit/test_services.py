import pytest

from overload_web.application import services, unit_of_work
from overload_web.domain import match_service


class FakeBibFetcher(match_service.BibFetcher):
    def get_bibs_by_id(self, value, key):
        bib_1 = {"bib_id": "123", "isbn": "9781234567890"}
        bib_2 = {"bib_id": "234", "isbn": "1234567890", "oclc_number": "123456789"}
        bib_3 = {
            "bib_id": "345",
            "isbn": "9781234567890",
            "oclc_number": "123456789",
        }
        bib_4 = {"bib_id": "456", "upc": "333"}
        return [bib_1, bib_2, bib_3, bib_4]


class MockUnitOfWork(unit_of_work.UnitOfWorkProtocol):
    def __init__(self):
        self.session = None
        self.sierra_session = None
        self.db_bibs = []
        self.bibs = FakeBibFetcher()

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


@pytest.mark.usefixtures("mock_sierra_response")
@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestApplicationServices:
    def test_get_bibs_by_key(self, bib_data, library):
        bib_data["isbn"] = "9781234567890"
        bibs = services.get_bibs_by_key(
            uow=MockUnitOfWork(), bib=bib_data, matchpoints=["isbn"]
        )
        assert len(bibs) == 4
        assert bibs == [
            {"bib_id": "123", "isbn": "9781234567890"},
            {"bib_id": "234", "isbn": "1234567890", "oclc_number": "123456789"},
            {
                "bib_id": "345",
                "isbn": "9781234567890",
                "oclc_number": "123456789",
            },
            {"bib_id": "456", "upc": "333"},
        ]

    def test_get_bibs_by_key_None(self, bib_data, library):
        bibs = services.get_bibs_by_key(
            uow=MockUnitOfWork(),
            bib=bib_data,
            matchpoints=["isbn"],
        )
        assert bibs == []

    def test_match_bib(self, bib_data, library):
        bib_data["isbn"] = "9781234567890"
        matched_bib = services.match_bib(
            uow=MockUnitOfWork(),
            bib=bib_data,
            matchpoints=["bib_id", "upc", "isbn", "oclc_number"],
        )
        assert matched_bib["bib_id"] == "123"
