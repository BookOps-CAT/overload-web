import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application import ports
from overload_web.application.pvf.file_handling import (
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
        UploadFileToWorkflow.execute(
            workflow_id="12345",
            filename="qux.mrc",
            content=b"",
            source=source,
            storage=storage,
            repo=repo,
        )
        assert "File added to workflow 12345: IncomingFile(id=" in caplog.text
        assert "Local file storage location: " in caplog.text

    def test_delete_file(self, test_session):
        repo = file_io.IncomingFileRepository(session=test_session)
        files = DeleteFileFromWorkflow.execute(id="1", repo=repo, workflow_id="12345")
        assert len(files) == 1
        assert files[0]["filename"] == "bar.mrc"


class TestLocalFiles:
    def test_local_objs(self):
        retriever = file_io.LocalFileRetriever()
        writer = file_io.LocalFileWriter()
        assert isinstance(retriever, ports.FileRetriever)
        assert isinstance(writer, ports.FileWriter)

    def test_local_download(self, tmp_path, tmp_files):
        retriever = file_io.LocalFileRetriever()
        loaded_file = retriever.download("foo.mrc", dir=tmp_path)
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

    def test_sftp_retriever(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever(client=mock_sftp_client)
        assert isinstance(retriever, ports.FileRetriever)
        assert hasattr(retriever, "list")
        assert hasattr(retriever, "download")
        assert retriever.client.name == "FOO"
        assert isinstance(retriever, ports.FileRetriever)

    def test_sftp_writer(self, mock_sftp_client):
        writer = file_io.SFTPFileWriter(client=mock_sftp_client)
        assert isinstance(writer, ports.FileWriter)
        assert hasattr(writer, "write")
        assert writer.client.name == "FOO"
        assert isinstance(writer, ports.FileWriter)

    def test_sftp_list(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever(client=mock_sftp_client)
        file_list = retriever.list(dir="test")
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_sftp_download(self, mock_sftp_client):
        retriever = file_io.SFTPFileRetriever(client=mock_sftp_client)
        file = retriever.download(name="foo.mrc", dir="test")
        assert file == b""

    def test_sftp_write(self, mock_sftp_client):
        writer = file_io.SFTPFileWriter(client=mock_sftp_client)
        out_file = writer.write(file=b"foo", file_name="foo.mrc", dir="test")
        assert out_file == "foo.mrc"
