import os

import pytest

from overload_web.infrastructure import file_io


@pytest.fixture
def tmp_files(tmp_path):
    file1 = tmp_path / "foo.mrc"
    file1.write_bytes(b"333331234567890")
    file2 = tmp_path / "bar.mrc"
    file2.write_bytes(b"333339876543210")


class TestLocalFiles:
    def test_local_download(self, tmp_path, tmp_files):
        retriever = file_io.LocalFileRetriever()
        loaded_file = retriever.download(name="foo.mrc", dir=tmp_path)
        assert "333331234567890".encode() in loaded_file
        assert "foo.mrc" in os.listdir(tmp_path)

    def test_local_list(self, tmp_path, tmp_files):
        retriever = file_io.LocalFileRetriever()
        file_list = retriever.list(dir=tmp_path)
        assert len(file_list) == 2
        assert "foo.mrc" in file_list

    def test_local_write(self, tmp_path):
        writer = file_io.LocalFileWriter()
        new_file = writer.write(
            file=b"333331234567890", file_name="foo.mrc", dir=tmp_path
        )
        assert new_file == os.path.join(tmp_path, "foo.mrc")
        assert "foo.mrc" in os.listdir(tmp_path)
        assert "333331234567890".encode() in open(new_file, "rb").read()


class TestRemoteFiles:
    def test_sftp_retriever(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever(client=mock_sftp_client)
        assert hasattr(retriever, "list")
        assert hasattr(retriever, "download")
        assert retriever.client.name == "FOO"

    def test_sftp_list(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever(client=mock_sftp_client)
        file_list = retriever.list(dir="test")
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_sftp_download(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever(client=mock_sftp_client)
        file = retriever.download(name="foo.mrc", dir="test")
        assert file == b""
