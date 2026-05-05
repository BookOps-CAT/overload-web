import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application import ports
from overload_web.application.commands.file_io import (
    DeleteFileFromWorkflow,
    LoadAllWorkflowFiles,
    UploadFileToWorkflow,
)
from overload_web.infrastructure import file_io


@pytest.fixture
def tmp_files(tmp_path):
    file1 = tmp_path / "foo.mrc"
    file1.write_bytes(b"333331234567890")
    file2 = tmp_path / "bar.mrc"
    file2.write_bytes(b"333339876543210")


@pytest.fixture
def test_session(tmp_path):
    file1 = file_io.IncomingFileModel(
        id="1",
        filename="foo.mrc",
        workflow_id="12345",
        source="ftp",
        reference=f"{tmp_path}/foo.mrc",
    )
    file2 = file_io.IncomingFileModel(
        id="2",
        filename="bar.mrc",
        workflow_id="12345",
        source="ftp",
        reference=f"{tmp_path}/bar.mrc",
    )
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        session.add(file1)
        session.commit()
        session.add(file2)
        session.commit()
        yield session
    session.close()
    test_engine.dispose()


class TestFileWorkflow:
    def test_load_all_files(self, test_session, caplog, tmp_path, tmp_files):
        path = tmp_path / "temp"
        storage = file_io.LocalFileStorage(base_path=path)
        repo = file_io.IncomingFileRepository(session=test_session)
        files = LoadAllWorkflowFiles.execute(
            workflow_id="12345", storage=storage, repo=repo
        )
        assert len(caplog.records) == 2
        assert "Local file storage location: " in caplog.records[0].message
        assert (
            f"Loading all files for workflow 12345: {files}."
            in caplog.records[1].message
        )

    @pytest.mark.parametrize("source", ["local", "ftp"])
    def test_upload_files(self, test_session, tmp_path, tmp_files, caplog, source):
        path = tmp_path / "temp"
        repo = file_io.IncomingFileRepository(session=test_session)
        storage = file_io.LocalFileStorage(base_path=path)
        UploadFileToWorkflow(storage=storage, repo=repo).execute(
            workflow_id="12345", filename="qux.mrc", content=b"", source=source
        )
        assert "File added to workflow 12345: IncomingFile(id=" in caplog.text
        assert "Local file storage location: " in caplog.text

    def test_delete_file(self, test_session):
        repo = file_io.IncomingFileRepository(session=test_session)
        DeleteFileFromWorkflow.execute(id="1", repo=repo)


class TestLocalFiles:
    def test_local_objs(self):
        loader = file_io.LocalFileLoader()
        writer = file_io.LocalFileWriter()
        assert isinstance(loader, ports.FileLoader)
        assert isinstance(writer, ports.FileWriter)

    def test_local_load(self, tmp_path, tmp_files):
        loader = file_io.LocalFileLoader()
        loaded_file = loader.load("foo.mrc", dir=tmp_path)
        assert "333331234567890".encode() in loaded_file
        assert "foo.mrc" in os.listdir(tmp_path)

    def test_local_list(self, tmp_path, tmp_files):
        loader = file_io.LocalFileLoader()
        file_list = loader.list(dir=tmp_path)
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

    def test_sftp_loader(self, mock_sftp_client):
        loader = file_io.SFTPFileLoader(client=mock_sftp_client)
        assert isinstance(loader, ports.FileLoader)
        assert hasattr(loader, "list")
        assert hasattr(loader, "load")
        assert loader.client.name == "FOO"
        assert isinstance(loader, ports.FileLoader)

    def test_sftp_writer(self, mock_sftp_client):
        writer = file_io.SFTPFileWriter(client=mock_sftp_client)
        assert isinstance(writer, ports.FileWriter)
        assert hasattr(writer, "write")
        assert writer.client.name == "FOO"
        assert isinstance(writer, ports.FileWriter)

    def test_sftp_list(self, mock_sftp_client):
        loader = file_io.SFTPFileLoader(client=mock_sftp_client)
        file_list = loader.list(dir="test")
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_sftp_load(self, mock_sftp_client):
        loader = file_io.SFTPFileLoader(client=mock_sftp_client)
        file = loader.load(name="foo.mrc", dir="test")
        assert file == b""

    def test_sftp_write(self, mock_sftp_client):
        writer = file_io.SFTPFileWriter(client=mock_sftp_client)
        out_file = writer.write(file=b"foo", file_name="foo.mrc", dir="test")
        assert out_file == "foo.mrc"
