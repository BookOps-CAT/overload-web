from overload_web.application import ports
from overload_web.application.commands.file_io import (
    ListVendorFiles,
    LoadVendorFile,
    WriteFile,
)
from overload_web.domain.models import files


class StubFileLoader(ports.FileLoader):
    def __init__(self) -> None:
        pass


class StubFileWriter(ports.FileWriter):
    def __init__(self) -> None:
        pass


class FakeFileLoader(StubFileLoader):
    def __init__(self) -> None:
        pass

    def list(self, dir: str) -> list[str]:
        return ["foo.mrc"]

    def load(self, name: str, dir: str) -> bytes:
        return b""


class FakeFileWriter(StubFileWriter):
    def __init__(self) -> None:
        pass

    def write(self, file: bytes, file_name: str, dir: str) -> str:
        return file_name


class TestFileTransferServices:
    loader = FakeFileLoader()

    def test_service_protocols(self):
        assert LoadVendorFile.execute(
            name="foo.mrc", dir="foo", loader=StubFileLoader()
        ) == files.VendorFile(content=None, file_name="foo.mrc")
        assert ListVendorFiles.execute(dir="foo", loader=StubFileLoader()) is None

    def test_list_files(self):
        file_list = ListVendorFiles.execute(dir="foo", loader=self.loader)
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_load_file(self):
        file = LoadVendorFile.execute(name="foo.mrc", dir="foo", loader=self.loader)
        assert file.file_name == "foo.mrc"
        assert file.content == b""


class TestFileWriterServices:
    writer = FakeFileWriter()

    def test_service_protocols(self):
        assert (
            WriteFile.execute(
                file_name="foo.mrc", file=b"", dir="bar", writer=StubFileWriter()
            )
            is None
        )

    def test_write_marc_file(self):
        out_file = WriteFile.execute(
            file=b"", file_name="foo.mrc", dir="bar", writer=self.writer
        )
        assert out_file == "foo.mrc"
