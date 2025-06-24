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
    def test_sftp_loader(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(client=mock_sftp_client)
        assert isinstance(loader, protocols.file_io.FileLoader)
        assert hasattr(loader, "list")
        assert hasattr(loader, "load")
        assert loader.client.name == "FOO"
        assert loader.base_dir == "nsdrop/vendor_files/foo"
        assert isinstance(loader, protocols.file_io.FileLoader)

    def test_sftp_loader_with_base_dir(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(
            client=mock_sftp_client, base_dir="nsdrop/vendor_files/test"
        )
        assert isinstance(loader, protocols.file_io.FileLoader)
        assert hasattr(loader, "list")
        assert hasattr(loader, "load")
        assert loader.client.name == "FOO"
        assert loader.base_dir == "nsdrop/vendor_files/test"
        assert os.environ["FOO_DST"] == "nsdrop/vendor_files/foo"
        assert isinstance(loader, protocols.file_io.FileLoader)

    def test_sftp_writer(self, mock_sftp_client):
        writer = file_io.sftp.SFTPFileWriter(client=mock_sftp_client)
        assert isinstance(writer, protocols.file_io.FileWriter)
        assert hasattr(writer, "write")
        assert writer.client.name == "FOO"
        assert writer.base_dir == "nsdrop/vendor_files/foo"
        assert isinstance(writer, protocols.file_io.FileWriter)

    def test_sftp_writer_with_base_dir(self, mock_sftp_client):
        writer = file_io.sftp.SFTPFileWriter(
            client=mock_sftp_client, base_dir="nsdrop/vendor_files/test"
        )
        assert isinstance(writer, protocols.file_io.FileWriter)
        assert hasattr(writer, "write")
        assert writer.client.name == "FOO"
        assert writer.base_dir == "nsdrop/vendor_files/test"
        assert os.environ["FOO_DST"] == "nsdrop/vendor_files/foo"
        assert isinstance(writer, protocols.file_io.FileWriter)

    def test_list(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(client=mock_sftp_client)
        file_list = loader.list()
        assert len(file_list) == 1
        assert file_list[0].file_id == "foo.mrc"
        assert file_list[0].name == "foo.mrc"

    def test_load(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(client=mock_sftp_client)
        file = loader.load(name="foo.mrc")
        assert file.content == b""
        assert file.file_id == "foo.mrc"

    def test_write(self, mock_sftp_client):
        writer = file_io.sftp.SFTPFileWriter(client=mock_sftp_client)
        out_file = writer.write(
            file=dto.file.FileContentDTO(file_id="foo.mrc", content=b"foo")
        )
        assert out_file == "foo.mrc"
