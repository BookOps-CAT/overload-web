import pytest

from overload_web.application import services, unit_of_work
from overload_web.infrastructure import sierra_adapters


def fake_sierra_service():
    class FakeSierraService(sierra_adapters.AbstractService):
        def _get_bibs_by_id(self, value, key):
            return [{"id": "123456789", key: value}]

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


class TestAbstractUnitOfWork:
    def test_commit(self):
        unit_of_work.AbstractUnitOfWork.__abstractmethods__ = set()
        uow = unit_of_work.AbstractUnitOfWork()
        with pytest.raises(NotImplementedError):
            uow.commit()

    def test_rollback(self):
        unit_of_work.AbstractUnitOfWork.__abstractmethods__ = set()
        uow = unit_of_work.AbstractUnitOfWork()
        with pytest.raises(NotImplementedError):
            uow.rollback()


@pytest.mark.usefixtures("mock_sierra_response")
@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestApplicationServices:
    def test_get_bibs_by_key(self, bib_data, library):
        bib_data["isbn"] = "9781234567890"
        bibs = services.get_bibs_by_key(
            uow=MockUnitOfWork(), bib=bib_data, matchpoints=["isbn"]
        )
        assert bibs == [
            {
                "library": library,
                "orders": [],
                "bib_id": "123456789",
                "isbn": "9781234567890",
                "oclc_number": None,
                "upc": None,
            }
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
        assert matched_bib["bib_id"] == "123456789"
