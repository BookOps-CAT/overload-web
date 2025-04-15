import pytest

from overload_web.adapters import sierra_adapters
from overload_web.services import handlers, unit_of_work


class FakeSierraService(sierra_adapters.AbstractService):
    def _get_bibs_by_id(self, value, key):
        return [{"id": "123456789"}]


@pytest.fixture
def stub_sierra_service(mock_sierra_response):
    return FakeSierraService()


def fake_sierra_service():
    class FakeSierraService(sierra_adapters.AbstractService):
        def _get_bibs_by_id(self, value, key):
            return [{"id": "123456789"}]

    return FakeSierraService()


class MockUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.session = None
        self.sierra_session = None
        self.db_bibs = []
        self.bibs = fake_sierra_service()

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


@pytest.mark.usefixtures("mock_sierra_response")
@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestServices:
    def test_match_bib(self, bib_data, library):
        bib_data["isbn"] = "9781234567890"
        matched_bib = handlers.match_bib(
            uow=MockUnitOfWork(),
            bib=bib_data,
            matchpoints=["bib_id", "upc", "isbn", "oclc_number"],
        )
        assert matched_bib["bib_id"] == "123456789"
