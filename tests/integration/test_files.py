import os

import pytest

from overload_web.application import dto
from overload_web.domain import models, protocols
from overload_web.infrastructure import file_io


@pytest.fixture
def stub_file(content, file_name):
    return models.files.VendorFile.create(content=content, file_name=file_name)


@pytest.fixture
def tmp_file(tmp_path, stub_binary_marc, library):
    file = tmp_path / "foo.mrc"
    file.write_bytes(stub_binary_marc.read())


class TestLocalFiles:
    def test_local_objs(self, tmp_path):
        loader = file_io.local.LocalFileLoader(base_dir=tmp_path)
        writer = file_io.local.LocalFileWriter(base_dir=tmp_path)
        assert isinstance(loader, protocols.file_io.FileLoader)
        assert isinstance(writer, protocols.file_io.FileWriter)

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_load(self, tmp_path, tmp_file):
        loader = file_io.local.LocalFileLoader(base_dir=tmp_path)
        loaded_file = loader.load("foo.mrc")
        assert "333331234567890".encode() in loaded_file.content
        assert "foo.mrc" in os.listdir(tmp_path)

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_list(self, tmp_path, tmp_file):
        loader = file_io.local.LocalFileLoader(base_dir=tmp_path)
        file_list = loader.list()
        assert len(file_list) == 1
        assert file_list[0].name == "foo.mrc"
        assert file_list[0].file_id == os.path.join(tmp_path, "foo.mrc")

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_write(self, tmp_path, stub_binary_marc):
        file_dto = dto.file.FileContentDTO(
            file_id="foo.mrc", content=stub_binary_marc.read()
        )
        writer = file_io.local.LocalFileWriter(base_dir=tmp_path)
        new_file = writer.write(file=file_dto)
        assert new_file == os.path.join(tmp_path, "foo.mrc")
        assert "foo.mrc" in os.listdir(tmp_path)
        assert "333331234567890".encode() in open(new_file, "rb").read()


class TestSFTPFiles:
    def test_sftp_objs(self):
        loader = file_io.sftp.SFTPFileLoader()
        writer = file_io.sftp.SFTPFileWriter()
        assert isinstance(loader, protocols.file_io.FileLoader)
        assert isinstance(writer, protocols.file_io.FileWriter)
