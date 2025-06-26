import os

import pytest

from overload_web.domain import models, protocols
from overload_web.infrastructure import file_io


@pytest.fixture
def tmp_file(tmp_path, stub_binary_marc, library):
    file = tmp_path / "foo.mrc"
    file.write_bytes(stub_binary_marc.read())


class TestLocalFiles:
    def stub_file(self, content, file_name):
        return models.files.VendorFile.create(content=content, file_name=file_name)

    def test_local_objs(self, tmp_path):
        loader = file_io.local.LocalFileLoader()
        writer = file_io.local.LocalFileWriter()
        assert isinstance(loader, protocols.file_io.FileLoader)
        assert isinstance(writer, protocols.file_io.FileWriter)

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_load(self, tmp_path, tmp_file):
        loader = file_io.local.LocalFileLoader()
        loaded_file = loader.load("foo.mrc", dir=tmp_path)
        assert "333331234567890".encode() in loaded_file.content
        assert "foo.mrc" in os.listdir(tmp_path)

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_list(self, tmp_path, tmp_file):
        loader = file_io.local.LocalFileLoader()
        file_list = loader.list(dir=tmp_path)
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_write(self, tmp_path, stub_binary_marc):
        out_file = self.stub_file(content=stub_binary_marc.read(), file_name="foo.mrc")
        writer = file_io.local.LocalFileWriter()
        new_file = writer.write(file=out_file, dir=tmp_path)
        assert new_file == os.path.join(tmp_path, "foo.mrc")
        assert "foo.mrc" in os.listdir(tmp_path)
        assert "333331234567890".encode() in open(new_file, "rb").read()


class TestSFTPFiles:
    def stub_file(self, content, file_name):
        return models.files.VendorFile.create(content=content, file_name=file_name)

    def test_sftp_loader(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(client=mock_sftp_client)
        assert isinstance(loader, protocols.file_io.FileLoader)
        assert hasattr(loader, "list")
        assert hasattr(loader, "load")
        assert loader.client.name == "FOO"
        assert isinstance(loader, protocols.file_io.FileLoader)

    def test_sftp_writer(self, mock_sftp_client):
        writer = file_io.sftp.SFTPFileWriter(client=mock_sftp_client)
        assert isinstance(writer, protocols.file_io.FileWriter)
        assert hasattr(writer, "write")
        assert writer.client.name == "FOO"
        assert isinstance(writer, protocols.file_io.FileWriter)

    def test_list(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(client=mock_sftp_client)
        file_list = loader.list(dir="test")
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_load(self, mock_sftp_client):
        loader = file_io.sftp.SFTPFileLoader(client=mock_sftp_client)
        file = loader.load(name="foo.mrc", dir="test")
        assert file.content == b""
        assert file.id is not None

    def test_write(self, mock_sftp_client):
        writer = file_io.sftp.SFTPFileWriter(client=mock_sftp_client)
        out_file = writer.write(
            file=self.stub_file(content=b"foo", file_name="foo.mrc"), dir="test"
        )
        assert out_file == "foo.mrc"
