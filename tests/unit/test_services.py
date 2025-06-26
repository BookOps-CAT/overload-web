import pytest

from overload_web.application import services
from overload_web.domain import models, protocols
from overload_web.infrastructure.bibs import sierra


class MockRepository(protocols.repositories.SqlRepositoryProtocol):
    def __init__(self, templates):
        self.templates = templates

    def get(self, id):
        return next((i for i in self.templates if i.id == id), None)

    def save(self, template):
        pass


class MockUnitOfWork(protocols.repositories.UnitOfWorkProtocol):
    def __init__(self):
        self.templates = MockRepository(templates=[])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestServices:
    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_attach_template(self, template_data, stub_bib_dto):
        original_domain_bib_fund = stub_bib_dto.domain_bib.orders[0].fund
        original_bib_fund = stub_bib_dto.bib.orders[0]._field.get("u", None)
        updated_bibs = services.services.attach_template(
            bibs=[stub_bib_dto], template=template_data
        )
        assert updated_bibs[0].domain_bib.orders[0] != original_domain_bib_fund
        assert updated_bibs[0].bib.orders[0]._field.get("u", None) != original_bib_fund

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_attach_template_empty_template(self, stub_bib_dto):
        updated_bibs = services.services.attach_template(
            bibs=[stub_bib_dto], template={}
        )
        assert updated_bibs[0].domain_bib.orders == stub_bib_dto.domain_bib.orders
        assert (
            updated_bibs[0].bib.orders[0].__dict__
            == stub_bib_dto.bib.orders[0].__dict__
        )

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_get_fetcher_for_library(self, library, mock_sierra_response):
        fetcher = services.services.get_fetcher_for_library(library=library)
        assert isinstance(fetcher, sierra.SierraBibFetcher)

    @pytest.mark.parametrize(
        "library, matchpoints, result",
        [
            ("bpl", ["isbn"], "123"),
            ("nypl", ["isbn"], "123"),
            ("bpl", ["isbn", "oclc_number"], "123"),
            ("nypl", ["isbn", "oclc_number"], "123"),
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
        bibs = services.services.match_bibs(
            bibs=[stub_bib_dto],
            matchpoints=matchpoints,
            fetcher=test_fetcher,
            library=library,
        )
        assert len(bibs) == 1
        assert str(bibs[0].bib.library) == library
        assert str(bibs[0].domain_bib.library) == library
        assert str(bibs[0].domain_bib.bib_id) == result

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_match_bibs_no_fetcher(self, stub_bib_dto, library, mock_sierra_response):
        bibs = services.services.match_bibs(
            bibs=[stub_bib_dto], matchpoints=["isbn"], library=library
        )
        assert len(bibs) == 1
        assert str(bibs[0].bib.library) == library
        assert str(bibs[0].domain_bib.library) == library
        assert str(bibs[0].domain_bib.bib_id) == "123456789"
        assert str(bibs[0].bib.sierra_bib_id) == "b123456789"

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def read_marc_binary(self, stub_binary_marc, library):
        dtos = []
        with open(stub_binary_marc, "rb") as f:
            dtos.append(services.services.read_marc_binary(f))
        assert len(dtos) == 1
        assert str(dtos[0].bib.library) == library
        assert dtos[0].bib.isbn == "9781234567890"
        assert str(dtos[0].domain_bib.library) == library
        assert dtos[0].domain_bib.barcodes == ["333331234567890"]

    def test_save_template(self, template_data):
        template_data.update({"name": "Foo", "agent": "Bar"})
        template_saver = services.services.save_template(
            data=template_data, uow=MockUnitOfWork()
        )
        assert template_saver == template_data

    def test_save_template_no_name(self, template_data):
        with pytest.raises(ValueError) as exc:
            services.services.save_template(data=template_data, uow=MockUnitOfWork())
        assert str(exc.value) == "Templates must have a name before being saved."

    def test_save_template_no_agent(self, template_data):
        template_data.update({"name": "Foo"})
        with pytest.raises(ValueError) as exc:
            services.services.save_template(data=template_data, uow=MockUnitOfWork())
        assert str(exc.value) == "Templates must have an agent before being saved."

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_write_marc_binary(self, stub_bib_dto, library):
        marc_binary = services.services.write_marc_binary(bibs=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"


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
