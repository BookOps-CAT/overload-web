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


class TestServices:
    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_attach_template(self, template_data, stub_bib_dto):
        original_domain_bib_fund = stub_bib_dto.domain_bib.orders[0].fund
        original_bib_fund = stub_bib_dto.bib.orders[0]._field.get("u", None)
        updated_bibs = services.attach_template(
            bibs=[stub_bib_dto], template=template_data
        )
        assert updated_bibs[0].domain_bib.orders[0] != original_domain_bib_fund
        assert updated_bibs[0].bib.orders[0]._field.get("u", None) != original_bib_fund

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_attach_template_empty_template(self, stub_bib_dto):
        updated_bibs = services.attach_template(bibs=[stub_bib_dto], template={})
        assert updated_bibs[0].domain_bib.orders == stub_bib_dto.domain_bib.orders
        assert (
            updated_bibs[0].bib.orders[0].__dict__
            == stub_bib_dto.bib.orders[0].__dict__
        )

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_get_fetcher_for_library(self, library, mock_sierra_response):
        fetcher = services.get_fetcher_for_library(library=library)
        assert isinstance(fetcher, sierra_adapters.SierraBibFetcher)

    @pytest.mark.parametrize(
        "library, matchpoints, result",
        [
            ("bpl", ["isbn"], "123"),
            ("nypl", ["isbn"], "123"),
            ("bpl", ["oclc_number"], None),
            ("nypl", ["oclc_number"], None),
            ("bpl", ["isbn", "oclc_number"], "123"),
            ("nypl", ["isbn", "oclc_number"], "123"),
            ("bpl", ["upc"], None),
            ("nypl", ["upc"], None),
        ],
    )
    def test_match_bibs(
        self,
        stub_bib_dto,
        test_fetcher,
        library,
        matchpoints,
        result,
    ):
        assert stub_bib_dto.domain_bib.bib_id is None
        assert stub_bib_dto.bib.sierra_bib_id is None
        bibs = services.match_bibs(
            bibs=[stub_bib_dto],
            matchpoints=matchpoints,
            fetcher=test_fetcher,
            library=library,
        )
        assert len(bibs) == 1
        assert bibs[0].bib.library == library
        assert bibs[0].domain_bib.library == library
        assert bibs[0].domain_bib.bib_id == result

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_match_bibs_no_fetcher(self, stub_bib_dto, library, mock_sierra_response):
        assert stub_bib_dto.domain_bib.bib_id is None
        assert stub_bib_dto.bib.sierra_bib_id is None
        bibs = services.match_bibs(
            bibs=[stub_bib_dto], matchpoints=["isbn"], library=library
        )
        assert len(bibs) == 1
        assert bibs[0].bib.library == library
        assert bibs[0].domain_bib.library == library
        assert bibs[0].domain_bib.bib_id == "123456789"
        assert bibs[0].bib.sierra_bib_id == "b123456789"

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def read_marc_binary(self, stub_binary_marc, library):
        dtos = []
        with open(stub_binary_marc, "rb") as f:
            dtos.append(services.read_marc_binary(f))
        assert len(dtos) == 1
        assert dtos[0].bib.library == library
        assert dtos[0].bib.isbn == "9781234567890"
        assert dtos[0].domain_bib.library == library
        assert dtos[0].domain_bib.barcodes == ["333331234567890"]

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

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_write_marc_binary(self, stub_bib_dto, library):
        marc_binary = services.write_marc_binary(bibs=[stub_bib_dto])
        assert marc_binary[0:2] == b"00"
