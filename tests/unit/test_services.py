import copy

import pytest

from overload_web.application import services
from overload_web.domain import logic, models, protocols
from overload_web.infrastructure.bibs import marc


class MockRepository(protocols.repositories.SqlRepositoryProtocol):
    def __init__(self, templates):
        self.templates = templates


class MockUnitOfWork(protocols.repositories.UnitOfWorkProtocol):
    def __init__(self):
        self.templates = MockRepository(templates=[])


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


@pytest.mark.parametrize("library", ["nypl", "bpl"])
class TestRecordProcessingService:
    def test_load(self, library, stub_binary_marc):
        service = services.records.RecordProcessingService(
            parser=marc.BookopsMarcParser(library=library),
            matcher=logic.bibs.BibMatcher(fetcher=StubFetcher(), matchpoints=[]),
            template={},
            library=library,
            matchpoints=[],
        )
        records = service.load(stub_binary_marc)
        assert len(records) == 1
        assert str(records[0].bib.library) == library
        assert records[0].bib.isbn == "9781234567890"
        assert str(records[0].domain_bib.library) == library
        assert records[0].domain_bib.barcodes == ["333331234567890"]

    @pytest.mark.parametrize(
        "matchpoints",
        [["isbn"], ["isbn", "oclc_number"]],
    )
    def test_process_records(self, matchpoints, library, stub_bib_dto):
        assert stub_bib_dto.domain_bib.bib_id is None
        assert stub_bib_dto.bib.sierra_bib_id is None
        service = services.records.RecordProcessingService(
            parser=marc.BookopsMarcParser(library=library),
            matcher=logic.bibs.BibMatcher(
                fetcher=FakeBibFetcher(), matchpoints=matchpoints
            ),
            template={},
            library=library,
            matchpoints=matchpoints,
        )
        matched_bibs = service.process_records([stub_bib_dto])
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"

    @pytest.mark.parametrize(
        "matchpoints",
        [["oclc_number"], ["upc"]],
    )
    def test_process_records_no_matched_bibs(self, matchpoints, library, stub_bib_dto):
        assert stub_bib_dto.domain_bib.bib_id is None
        assert stub_bib_dto.bib.sierra_bib_id is None
        service = services.records.RecordProcessingService(
            parser=marc.BookopsMarcParser(library=library),
            matcher=logic.bibs.BibMatcher(
                fetcher=FakeBibFetcher(), matchpoints=matchpoints
            ),
            template={},
            library=library,
            matchpoints=matchpoints,
        )
        matched_bibs = service.process_records([stub_bib_dto])
        assert len(matched_bibs) == 1
        assert matched_bibs[0].domain_bib.bib_id is None

    def test_process_records_no_results(self, library, stub_bib_dto):
        service = services.records.RecordProcessingService(
            parser=marc.BookopsMarcParser(library=library),
            matcher=logic.bibs.BibMatcher(fetcher=StubFetcher(), matchpoints=["isbn"]),
            template={},
            library=library,
            matchpoints=[],
        )
        matched_bibs = service.process_records([stub_bib_dto])
        assert len(matched_bibs) == 1
        assert matched_bibs[0].domain_bib.bib_id is None

    def test_process_records_with_fields(self, library, template_data, stub_bib_dto):
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
        service = services.records.RecordProcessingService(
            parser=marc.BookopsMarcParser(library=library),
            matcher=logic.bibs.BibMatcher(fetcher=StubFetcher(), matchpoints=["isbn"]),
            template=template_data,
            library=library,
            matchpoints=[],
        )
        updated = service.process_records(records=[stub_bib_dto])
        assert len(original_bib.get_fields("949")) == 1
        assert len(updated) == 1
        assert len(updated[0].bib.get_fields("949")) == 2

    def test_write_marc_binary(self, stub_bib_dto, library):
        service = services.records.RecordProcessingService(
            parser=marc.BookopsMarcParser(library=library),
            matcher=logic.bibs.BibMatcher(fetcher=StubFetcher(), matchpoints=["isbn"]),
            template={},
            library=library,
            matchpoints=[],
        )
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
