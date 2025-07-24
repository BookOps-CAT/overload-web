import copy

import pytest

from overload_web.application import services
from overload_web.domain import models, protocols


class MockRepository(protocols.repositories.SqlRepositoryProtocol):
    def __init__(self, templates):
        self.templates = templates


class StubFetcher(protocols.bibs.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def get_bibs_by_id(self, value, key):
        bib_1 = {"bib_id": "123", "isbn": "9781234567890"}
        bib_2 = {"bib_id": "234", "isbn": "1234567890", "oclc_number": "123456789"}
        bib_3 = {"bib_id": "345", "isbn": "9781234567890", "oclc_number": "123456789"}
        bib_4 = {"bib_id": "456", "upc": "333"}
        return [bib_1, bib_2, bib_3, bib_4]


@pytest.mark.parametrize(
    "library, collection, record_type",
    [
        ("nypl", "BL", "full"),
        ("nypl", "BL", "order_level"),
        ("nypl", "RL", "full"),
        ("nypl", "RL", "order_level"),
        ("bpl", "NONE", "full"),
        ("bpl", "NONE", "order_level"),
    ],
)
class TestRecordProcessingService:
    stub_mapping = {
        "907": {"a": "bib_id"},
        "960": {
            "c": "order_code_1",
            "d": "order_code_2",
            "e": "order_code_3",
            "f": "order_code_4",
            "g": "format",
            "i": "order_type",
            "m": "status",
            "o": "copies",
            "q": "create_date",
            "s": "price",
            "t": "locations",
            "u": "fund",
            "v": "vendor_code",
            "w": "lang",
            "x": "country",
            "z": "order_id",
        },
        "961": {
            "d": "internal_note",
            "f": "selector_note",
            "h": "vendor_notes",
            "i": "vendor_title_no",
            "l": "var_field_isbn",
            "m": "blanket_po",
        },
    }

    @pytest.fixture
    def stub_service(self, monkeypatch, library, collection, record_type):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher()

        monkeypatch.setattr(
            "overload_web.infrastructure.bibs.sierra.SierraBibFetcher", fake_fetcher
        )
        return services.records.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            marc_rules=self.stub_mapping,
        )

    @pytest.fixture
    def stub_service_no_matches(self, monkeypatch, library, collection, record_type):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.infrastructure.bibs.sierra.SierraBibFetcher", fake_fetcher
        )
        return services.records.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            marc_rules=self.stub_mapping,
        )

    @pytest.fixture
    def stub_bib_dto(self, library, make_bib_dto):
        dto = make_bib_dto({"020": {"code": "a", "value": "9781234567890"}})
        return dto

    def test_parse(self, stub_service, stub_bib_dto):
        records = stub_service.parse(stub_bib_dto.bib.as_marc())
        assert len(records) == 1
        assert str(records[0].bib.library) == str(stub_service.library)
        assert records[0].bib.isbn == "9781234567890"
        assert str(records[0].domain_bib.library) == str(stub_service.library)
        assert records[0].domain_bib.barcodes == ["333331234567890"]

    def test_process_records(self, stub_service, stub_bib_dto, template_data):
        original_orders = copy.deepcopy(stub_bib_dto.domain_bib.orders)
        matched_bibs = stub_service.process_records([stub_bib_dto], template_data)
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].domain_bib.orders] == ["b"]

    def test_process_records_template(self, stub_service, stub_bib_dto, template_data):
        matched_bibs = stub_service.process_records(
            [stub_bib_dto], template_data=models.templates.Template(**template_data)
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"

    def test_process_records_no_matches(self, stub_service_no_matches, stub_bib_dto):
        matched_bibs = stub_service_no_matches.process_records(
            [stub_bib_dto], template_data={}
        )
        assert len(matched_bibs) == 1
        assert matched_bibs[0].domain_bib.bib_id is None

    def test_process_records_vendor_updates(self, stub_service, make_bib_dto):
        dto = make_bib_dto(
            {
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(dto.bib)
        matched_bibs = stub_service.process_records([dto], template_data={})
        assert len(matched_bibs) == 1
        assert len(original_bib.get_fields("949")) == 1
        assert len(matched_bibs[0].bib.get_fields("949")) == 2

    def test_write_marc_binary(self, stub_bib_dto, stub_service):
        marc_binary = stub_service.write_marc_binary(records=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"


class TestTemplateService:
    @pytest.fixture
    def service(self, test_sql_session):
        return services.template.TemplateService(session=test_sql_session)

    def test_get_template(self, service):
        template_obj = service.get_template(template_id="foo")
        assert template_obj is None

    def test_list_templates(self, service):
        template_list = service.list_templates()
        assert template_list == []

    def test_save_template(self, service, template_data, make_template):
        template_data.update(
            {"name": "Foo", "agent": "Bar", "primary_matchpoint": "isbn"}
        )
        template = make_template(template_data)
        template_saver = service.save_template(obj=template)
        assert template_saver.name == template_data["name"]
        assert template_saver.agent == template_data["agent"]
        assert template_saver.blanket_po == template_data["blanket_po"]

    def test_save_template_no_name(self, service, template_data, make_template):
        template_data.update({"primary_matchpoint": "isbn"})
        template = make_template(template_data)
        with pytest.raises(ValueError) as exc:
            service.save_template(obj=template)
        assert str(exc.value) == "Templates must have a name before being saved."

    def test_save_template_no_agent(self, service, template_data, make_template):
        template_data.update({"name": "Foo", "primary_matchpoint": "isbn"})
        template = make_template(template_data)
        with pytest.raises(ValueError) as exc:
            service.save_template(obj=template)
        assert str(exc.value) == "Templates must have an agent before being saved."


class StubFileLoader(protocols.file_io.FileLoader):
    def __init__(self) -> None:
        pass


class StubFileWriter(protocols.file_io.FileWriter):
    def __init__(self) -> None:
        pass


class FakeFileLoader(StubFileLoader):
    def __init__(self) -> None:
        pass

    def list(self, dir: str) -> list[str]:
        return ["foo.mrc"]

    def load(self, name: str, dir: str) -> models.files.VendorFile:
        return models.files.VendorFile.create(file_name=name, content=b"")


class FakeFileWriter(StubFileWriter):
    def __init__(self) -> None:
        pass

    def write(self, file: models.files.VendorFile, dir: str) -> str:
        return file.file_name


class TestFileTransferServices:
    service = services.file.FileTransferService(
        loader=FakeFileLoader(), writer=FakeFileWriter()
    )

    def test_service_protocols(self):
        service = services.file.FileTransferService(
            loader=StubFileLoader(), writer=StubFileWriter()
        )
        vendor_file = models.files.VendorFile.create(file_name="foo.mrc", content=b"")
        assert service.load_file(name="foo.mrc", dir="foo") is None
        assert service.list_files(dir="foo") is None
        assert service.write_marc_file(file=vendor_file, dir="bar") is None

    def test_list_files(self):
        file_list = self.service.list_files(dir="foo")
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_load_file(self):
        file = self.service.load_file(name="foo.mrc", dir="foo")
        assert file.id is not None
        assert file.file_name == "foo.mrc"
        assert file.content == b""

    def test_write_marc_file(self):
        out_file = self.service.write_marc_file(
            file=models.files.VendorFile.create(file_name="foo.mrc", content=b""),
            dir="bar",
        )
        assert out_file == "foo.mrc"
