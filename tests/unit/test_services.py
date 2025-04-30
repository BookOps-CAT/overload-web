import pytest

from overload_web.application import services, unit_of_work
from overload_web.infrastructure import repository, sierra_adapters


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


@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestMatchServices:
    def test_get_fetcher_for_library(self, library, mock_sierra_response):
        fetcher = services.get_fetcher_for_library(library=library)
        assert isinstance(fetcher, sierra_adapters.SierraBibFetcher)

    @pytest.mark.parametrize(
        "matchpoints, result",
        [
            (["isbn"], "123"),
            (["oclc_number"], None),
            (["isbn", "oclc_number"], "123"),
            (["upc"], None),
        ],
    )
    def test_match_bibs(
        self,
        stub_binary_marc,
        library,
        test_fetcher,
        matchpoints,
        result,
    ):
        bibs = services.match_bibs(
            file_data=stub_binary_marc,
            matchpoints=matchpoints,
            fetcher=test_fetcher,
            library=library,
        )
        assert len(bibs) == 1
        assert bibs[0]["library"] == library
        assert bibs[0]["bib_id"] == result
        assert len(bibs[0]["orders"]) == 1

    def test_match_bibs_no_fetcher(
        self, stub_binary_marc, library, mock_sierra_response
    ):
        bibs = services.match_bibs(
            file_data=stub_binary_marc,
            matchpoints=["isbn"],
            library=library,
        )
        assert len(bibs) == 1
        assert bibs[0]["library"] == library
        assert bibs[0]["bib_id"] == "123456789"
        assert len(bibs[0]["orders"]) == 1

    @pytest.mark.parametrize(
        "matchpoints, result",
        [
            (["isbn"], "123"),
            (["oclc_number"], None),
            (["isbn", "oclc_number"], "123"),
            (["upc"], None),
        ],
    )
    def test_match_and_attach(
        self,
        stub_binary_marc,
        template_data,
        library,
        test_fetcher,
        matchpoints,
        result,
    ):
        bibs = services.match_and_attach(
            file_data=stub_binary_marc,
            template=template_data,
            matchpoints=matchpoints,
            fetcher=test_fetcher,
            library=library,
        )
        assert len(bibs) == 1
        assert bibs[0]["library"] == library
        assert bibs[0]["bib_id"] == result
        assert len(bibs[0]["orders"]) == 1

    def test_match_and_attach_no_fetcher(
        self, stub_binary_marc, template_data, library, mock_sierra_response
    ):
        bibs = services.match_and_attach(
            file_data=stub_binary_marc,
            template=template_data,
            matchpoints=["isbn"],
            library=library,
        )
        assert len(bibs) == 1
        assert bibs[0]["library"] == library
        assert bibs[0]["bib_id"] == "123456789"
        assert len(bibs[0]["orders"]) == 1


class TestTemplateServices:
    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_apply_template_data(self, template_data, bib_data):
        updated_bibs = services.apply_template_data(
            bib_data=[bib_data], template=template_data
        )
        assert [i["orders"][0]["fund"] for i in updated_bibs][0] == template_data[
            "fund"
        ]
        assert updated_bibs[0]["orders"] != bib_data["orders"]

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_apply_template_data_empty_template(self, bib_data):
        updated_bibs = services.apply_template_data(bib_data=[bib_data], template={})
        assert updated_bibs[0]["orders"] == bib_data["orders"]

    def test_save_template(self, template_data):
        template_data.update({"name": "Foo", "agent": "Bar"})
        template_saver = services.save_template(
            data=template_data, uow=MockUnitOfWork()
        )
        assert template_saver == template_data

    def test_save_template_no_name(self, template_data):
        with pytest.raises(ValueError) as exc:
            services.save_template(data=template_data, uow=MockUnitOfWork())
        assert str(exc.value) == "Templates must have a name before being saved."

    def test_save_template_no_agent(self, template_data):
        template_data.update({"name": "Foo"})
        with pytest.raises(ValueError) as exc:
            services.save_template(data=template_data, uow=MockUnitOfWork())
        assert str(exc.value) == "Templates must have an agent before being saved."
