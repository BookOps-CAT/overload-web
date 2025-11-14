from overload_web.application import file_service
from overload_web.domain import protocols
from overload_web.domain_models import files


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

    def load(self, name: str, dir: str) -> files.VendorFile:
        return files.VendorFile.create(file_name=name, content=b"")


class FakeFileWriter(StubFileWriter):
    def __init__(self) -> None:
        pass

    def write(self, file: files.VendorFile, dir: str) -> str:
        return file.file_name


class TestFileTransferServices:
    service = file_service.FileTransferService(
        loader=FakeFileLoader(), writer=FakeFileWriter()
    )

    def test_service_protocols(self):
        service = file_service.FileTransferService(
            loader=StubFileLoader(), writer=StubFileWriter()
        )
        vendor_file = files.VendorFile.create(file_name="foo.mrc", content=b"")
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
            file=files.VendorFile.create(file_name="foo.mrc", content=b""),
            dir="bar",
        )
        assert out_file == "foo.mrc"
