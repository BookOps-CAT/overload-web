import copy

import pytest

from overload_web.application import services
from overload_web.domain import logic, protocols
from overload_web.infrastructure.bibs import marc


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
    def stub_record_service(self, matchpoints, library):
        matcher = logic.bibs.BibMatcher(
            fetcher=FakeBibFetcher(), matchpoints=matchpoints
        )
        parser = marc.BookopsMarcTransformer(library=library)
        return services.records.RecordProcessingService(
            parser=parser, matcher=matcher, template={}
        )

    def test_RecordProcessingService(self, library):
        service = self.stub_record_service(["bib_id", "isbn"], library)
        assert hasattr(service, "load")
        assert hasattr(service, "match_records")
        assert hasattr(service, "update_bib")
        assert hasattr(service, "write_marc_binary")

    def test_load(self, library, stub_binary_marc):
        service = self.stub_record_service(["bib_id", "isbn"], library)
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
    def test_match_records(self, matchpoints, library, result, stub_bib_dto):
        assert stub_bib_dto.domain_bib.bib_id is None
        assert stub_bib_dto.bib.sierra_bib_id is None
        service = self.stub_record_service(matchpoints, library)
        matched_bibs = service.match_records([stub_bib_dto])
        assert len(matched_bibs) == 1
        assert matched_bibs[0].bib.library == library
        assert str(matched_bibs[0].domain_bib.library) == library
        assert (
            matched_bibs[0].domain_bib.bib_id == result
            if not matched_bibs[0].domain_bib.bib_id
            else str(matched_bibs[0].domain_bib.bib_id) == result
        )

    def test_update_bib(self, library, template_data, stub_bib_dto):
        service = self.stub_record_service(["isbn"], library)
        original_domain_bib_fund = stub_bib_dto.domain_bib.orders[0].fund
        original_bib_fund = stub_bib_dto.bib.orders[0]._field.get("u", None)
        updated_bibs = service.update_bib(
            records=[stub_bib_dto], template=template_data
        )
        assert updated_bibs[0].domain_bib.orders[0] != original_domain_bib_fund
        assert updated_bibs[0].bib.orders[0]._field.get("u", None) != original_bib_fund

    def test_update_bib_empty_template(self, library, stub_bib_dto):
        service = self.stub_record_service(["isbn"], library)
        updated_bibs = service.update_bib(records=[stub_bib_dto], template={})
        assert updated_bibs[0].domain_bib.orders == stub_bib_dto.domain_bib.orders
        assert (
            updated_bibs[0].bib.orders[0].__dict__
            == stub_bib_dto.bib.orders[0].__dict__
        )

    def test_update_bib_field_template_with_fields(
        self, library, template_data, stub_bib_dto
    ):
        original_bib = copy.deepcopy(stub_bib_dto.bib)
        template_data["update_fields"] = [
            {
                "tag": "949",
                "ind1": "",
                "ind2": "",
                "subfield_code": "a",
                "value": "*b2=a;",
            },
        ]
        service = self.stub_record_service(["isbn"], library)
        updated = service.update_bib(records=[stub_bib_dto], template=template_data)
        assert len(original_bib.get_fields("949")) == 1
        assert len(updated) == 1
        assert len(updated[0].bib.get_fields("949")) == 2

    def test_write_marc_binary(self, stub_bib_dto, library):
        service = self.stub_record_service(["isbn"], library)
        marc_binary = service.write_marc_binary(records=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"


class TestTemplateService:
    @pytest.fixture
    def service(self):
        return services.template.TemplateService(uow=MockUnitOfWork())

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
