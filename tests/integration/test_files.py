import os

import pytest

from overload_web.domain.models import vendor_files
from overload_web.infrastructure.storage import local_io, sftp


@pytest.fixture
def tmp_file(tmp_path):
    file = tmp_path / "foo.mrc"
    file.write_bytes(b"333331234567890")


class TestLocalFiles:
    def fake_file(self, content, file_name):
        return vendor_files.VendorFile(content=content, file_name=file_name)

    def test_local_objs(self, tmp_path):
        loader = local_io.LocalFileLoader()
        writer = local_io.LocalFileWriter()
        assert isinstance(loader, vendor_files.FileLoader)
        assert isinstance(writer, vendor_files.FileWriter)

    def test_local_load(self, tmp_path, tmp_file):
        loader = local_io.LocalFileLoader()
        loaded_file = loader.load("foo.mrc", dir=tmp_path)
        assert "333331234567890".encode() in loaded_file.content
        assert "foo.mrc" in os.listdir(tmp_path)

    def test_local_list(self, tmp_path, tmp_file):
        loader = local_io.LocalFileLoader()
        file_list = loader.list(dir=tmp_path)
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_local_write(self, tmp_path):
        out_file = self.fake_file(content=b"333331234567890", file_name="foo.mrc")
        writer = local_io.LocalFileWriter()
        new_file = writer.write(file=out_file, dir=tmp_path)
        assert new_file == os.path.join(tmp_path, "foo.mrc")
        assert "foo.mrc" in os.listdir(tmp_path)
        assert "333331234567890".encode() in open(new_file, "rb").read()

    def test_sftp_loader(self, mock_sftp_client):
        loader = sftp.SFTPFileLoader(client=mock_sftp_client)
        assert isinstance(loader, vendor_files.FileLoader)
        assert hasattr(loader, "list")
        assert hasattr(loader, "load")
        assert loader.client.name == "FOO"
        assert isinstance(loader, vendor_files.FileLoader)

    def test_sftp_writer(self, mock_sftp_client):
        writer = sftp.SFTPFileWriter(client=mock_sftp_client)
        assert isinstance(writer, vendor_files.FileWriter)
        assert hasattr(writer, "write")
        assert writer.client.name == "FOO"
        assert isinstance(writer, vendor_files.FileWriter)

    def test_sftp_list(self, mock_sftp_client):
        loader = sftp.SFTPFileLoader(client=mock_sftp_client)
        file_list = loader.list(dir="test")
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_sftp_load(self, mock_sftp_client):
        loader = sftp.SFTPFileLoader(client=mock_sftp_client)
        file = loader.load(name="foo.mrc", dir="test")
        assert file.content == b""

    def test_sftp_write(self, mock_sftp_client):
        writer = sftp.SFTPFileWriter(client=mock_sftp_client)
        out_file = writer.write(
            file=self.fake_file(content=b"foo", file_name="foo.mrc"), dir="test"
        )
        assert out_file == "foo.mrc"
