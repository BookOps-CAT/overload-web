import pytest

from overload_web.application import services, unit_of_work
from overload_web.domain import match_service
from overload_web.infrastructure import repository


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


class MockRepository(repository.RepositoryProtocol):
    def __init__(self, templates):
        self.templates = templates

    def get(self, id):
        return next((i for i in self.templates if i.id == id), None)

    def save(self, template):
        pass


class MockUnitOfWork(unit_of_work.UnitOfWorkProtocol):
    def __init__(self):
        self.templates = MockRepository(templates=[])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_OverloadUnitOfWork():
    with unit_of_work.OverloadUnitOfWork() as uow:
        uow.commit()
        uow.rollback()


@pytest.mark.usefixtures("mock_sierra_response")
@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestApplicationServices:
    def test_apply_template_data(self, template_data, bib_data, library):
        updated_bibs = services.apply_template_data(
            bib_data=[bib_data], template=template_data
        )
        assert [i["orders"][0]["fund"] for i in updated_bibs][0] == template_data[
            "fund"
        ]
        assert updated_bibs[0]["orders"] != bib_data["orders"]

    def test_apply_template_data_empty_template(self, bib_data, library):
        updated_bibs = services.apply_template_data(bib_data=[bib_data], template={})
        assert updated_bibs[0]["orders"] == bib_data["orders"]

    def test_match_bib(self, bib_data, library):
        bib_data["isbn"] = "9781234567890"
        matched_bib = services.match_bib(
            fetcher=FakeBibFetcher(),
            bib=bib_data,
            matchpoints=["bib_id", "upc", "isbn", "oclc_number"],
        )
        assert matched_bib["bib_id"] == "123"

    def test_save_template(self, template_data, library):
        template_data.update({"name": "Foo", "agent": "Bar"})
        template_saver = services.save_template(
            data=template_data, uow=MockUnitOfWork()
        )
        assert template_saver == template_data

    def test_save_template_no_name(self, template_data, library):
        with pytest.raises(ValueError) as exc:
            services.save_template(data=template_data, uow=MockUnitOfWork())
        assert str(exc.value) == "Templates must have a name before being saved."

    def test_save_template_no_agent(self, template_data, library):
        template_data.update({"name": "Foo"})
        with pytest.raises(ValueError) as exc:
            services.save_template(data=template_data, uow=MockUnitOfWork())
        assert str(exc.value) == "Templates must have an agent before being saved."
