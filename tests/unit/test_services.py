import pytest

from overload_web.application.services import records, template
from overload_web.domain import logic, protocols
from overload_web.infrastructure.bibs import marc_adapters


class MockRepository(protocols.repositories.SqlRepositoryProtocol):
    def __init__(self, templates):
        self.templates = templates


class MockUnitOfWork(protocols.repositories.UnitOfWorkProtocol):
    def __init__(self):
        self.templates = MockRepository(templates=[])
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True


class FakeBibFetcher(protocols.bibs.BibFetcher):
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


@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestRecordProcessingService:
    @pytest.fixture
    def record_service_factory(self):
        def _make_service(matchpoints, library):
            matcher = logic.bibs.BibMatcher(
                fetcher=FakeBibFetcher(), matchpoints=matchpoints
            )
            parser = marc_adapters.BookopsMarcTransformer(library=library)
            return records.RecordProcessingService(
                parser=parser, matcher=matcher, template={}
            )

        return _make_service

    def test_RecordProcessingService(self, record_service_factory, library):
        service = record_service_factory(["bib_id", "isbn"], library)
        assert hasattr(service, "load")
        assert hasattr(service, "match_records")
        assert hasattr(service, "update_bib_fields")
        assert hasattr(service, "write_marc_binary")

    def test_load(self, record_service_factory, library, stub_binary_marc):
        service = record_service_factory(["bib_id", "isbn"], library)
        records = service.load(stub_binary_marc)
        assert len(records) == 1
        assert str(records[0].bib.library) == library
        assert records[0].bib.isbn == "9781234567890"
        assert str(records[0].domain_bib.library) == library
        assert records[0].domain_bib.barcodes == ["333331234567890"]

    @pytest.mark.parametrize(
        "matchpoints, result",
        [
            (["isbn"], "123"),
            (["oclc_number"], None),
            (["isbn", "oclc_number"], "123"),
            (["upc"], None),
        ],
    )
    def test_match_records(
        self, record_service_factory, matchpoints, library, result, stub_bib_dto
    ):
        assert stub_bib_dto.domain_bib.bib_id is None
        assert stub_bib_dto.bib.sierra_bib_id is None
        service = record_service_factory(matchpoints, library)
        matched_bibs = service.match_records([stub_bib_dto])
        assert len(matched_bibs) == 1
        assert matched_bibs[0].bib.library == library
        assert str(matched_bibs[0].domain_bib.library) == library
        assert (
            matched_bibs[0].domain_bib.bib_id == result
            if not matched_bibs[0].domain_bib.bib_id
            else str(matched_bibs[0].domain_bib.bib_id) == result
        )

    def test_update_bib_fields(
        self, record_service_factory, library, template_data, stub_bib_dto
    ):
        service = record_service_factory(["isbn"], library)
        original_domain_bib_fund = stub_bib_dto.domain_bib.orders[0].fund
        original_bib_fund = stub_bib_dto.bib.orders[0]._field.get("u", None)
        updated_bibs = service.update_bib_fields(
            records=[stub_bib_dto], template=template_data
        )
        assert updated_bibs[0].domain_bib.orders[0] != original_domain_bib_fund
        assert updated_bibs[0].bib.orders[0]._field.get("u", None) != original_bib_fund

    def test_update_bib_fields_empty_template(
        self, record_service_factory, library, stub_bib_dto
    ):
        service = record_service_factory(["isbn"], library)
        updated_bibs = service.update_bib_fields(records=[stub_bib_dto], template={})
        assert updated_bibs[0].domain_bib.orders == stub_bib_dto.domain_bib.orders
        assert (
            updated_bibs[0].bib.orders[0].__dict__
            == stub_bib_dto.bib.orders[0].__dict__
        )

    def test_write_marc_binary(self, record_service_factory, stub_bib_dto, library):
        service = record_service_factory(["isbn"], library)
        marc_binary = service.write_marc_binary(records=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"


class TestTemplateService:
    @pytest.fixture
    def service(self):
        return template.TemplateService(uow=MockUnitOfWork())

    def test_get_template(self, service):
        template_obj = service.get_template(template_id="foo")
        assert template_obj is None

    def test_save_template(self, service, template_data):
        template_data.update({"name": "Foo", "agent": "Bar"})
        template_saver = service.save_template(data=template_data)
        assert template_saver == template_data

    def test_save_template_no_name(self, service, template_data):
        with pytest.raises(ValueError) as exc:
            service.save_template(data=template_data)
        assert str(exc.value) == "Templates must have a name before being saved."

    def test_save_template_no_agent(self, service, template_data):
        template_data.update({"name": "Foo"})
        with pytest.raises(ValueError) as exc:
            service.save_template(data=template_data)
        assert str(exc.value) == "Templates must have an agent before being saved."
