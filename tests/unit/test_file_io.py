import io
import os

import pytest
from file_retriever import Client, File, FileInfo

from overload_web.domain.pvf import aggregate
from overload_web.infrastructure import file_io


@pytest.fixture
def tmp_files(tmp_path):
    file1 = tmp_path / "foo.mrc"
    file1.write_bytes(b"333331234567890")
    file2 = tmp_path / "bar.mrc"
    file2.write_bytes(b"333339876543210")


@pytest.fixture
def mock_read_file(mocker) -> None:
    mock_read = mocker.mock_open(read_data=b"foo")
    mocker.patch("overload_web.infrastructure.file_io.open", mock_read)


@pytest.fixture
def mock_sftp_client(monkeypatch):
    file_data = {"file_size": 140401, "file_mtime": 1704070800, "file_mode": 33188}

    def _get_file(*args, **kwargs):
        return File.from_fileinfo(file=kwargs["file"], file_stream=io.BytesIO(b""))

    def _get_file_info(*args, **kwargs):
        file_data["file_name"] = kwargs["file_name"]
        return FileInfo(**file_data)

    def _list_files(*args, **kwargs):
        return ["foo.mrc"]

    def _put_file(*args, **kwargs):
        file_data["file_name"] = kwargs["file"].file_name
        return FileInfo(**file_data)

    def null_return(*args, **kwargs):
        return None

    monkeypatch.setattr(Client, "get_file", _get_file)
    monkeypatch.setattr(Client, "get_file_info", _get_file_info)
    monkeypatch.setattr(Client, "list_files", _list_files)
    monkeypatch.setattr(Client, "put_file", _put_file)
    monkeypatch.setattr(Client, "_Client__connect_to_server", null_return)
    return Client(
        name="FOO", username="foo", password="bar", host="sftp.baz.com", port="22"
    )


class TestLocalFileRetriever:
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


class TestLocalFileWriter:
    def test_local_write(self, tmp_path):
        writer = file_io.LocalFileWriter()
        new_file = writer.write(
            file=b"333331234567890", file_name="foo.mrc", dir=tmp_path
        )
        assert new_file == os.path.join(tmp_path, "foo.mrc")
        assert "foo.mrc" in os.listdir(tmp_path)
        assert "333331234567890".encode() in open(new_file, "rb").read()


class TestSFTPFileRetriever:
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

    def test_create_retriever_for_vendor(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever.create_retriever_for_vendor(vendor="FOO")
        assert retriever.client.name == "FOO"


class TestLocalFileStorage:
    def test_save(self, tmp_path):
        path = tmp_path / "temp"
        storage = file_io.LocalFileStorage(base_path=path)
        saved_file = storage.save(id="12345", filename="foo.mrc", content=b"")
        assert saved_file.endswith("12345_foo.mrc")

    def test_load(self, tmp_path, mock_read_file):
        path = tmp_path / "temp"
        storage = file_io.LocalFileStorage(base_path=path)
        loaded_file = storage.load(reference="12345")
        assert loaded_file == b"foo"

    def test_save_intermediate_records(self, tmp_path):
        path = tmp_path / "temp"
        storage = file_io.LocalFileStorage(base_path=path)
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        storage.save_intermediate_records(id="12345", job=job)
        loaded = storage.load_intermediate_records(id="12345")
        assert loaded is not None

    def test_load_intermediate_records(self, tmp_path):
        path = tmp_path / "temp"
        storage = file_io.LocalFileStorage(base_path=path)
        with pytest.raises(FileNotFoundError) as exc:
            storage.load_intermediate_records(id="12345")
        assert str(exc.value) == "No intermediate state found for 12345."
