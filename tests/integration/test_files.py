from __future__ import annotations

import pytest
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf.file_handling import (
    DeleteFileFromWorkflow,
    DownloadRemoteFile,
    ListVendorFiles,
    UploadFileToWorkflow,
)
from overload_web.infrastructure import file_io, unit_of_work


class FakeFileRetriever:
    def __init__(self) -> None:
        pass

    def list(self, dir: str) -> list[str]:
        return ["foo.mrc"]

    def download(self, name: str, dir: str) -> bytes:
        return b""


@pytest.fixture
def mock_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


class MockSqlResult:
    FILE = file_io.IncomingFileModel(
        id="12345",
        filename="foo.mrc",
        workflow_id="12345",
        source="ftp",
        reference="temp/foo.mrc",
    )

    def all(self):
        return [self.FILE]

    def one_or_none(self):
        return self.FILE


@pytest.fixture
def mock_engine_with_files(monkeypatch, mock_engine):
    def mock_exec(*args, **kwargs):
        return MockSqlResult()

    def null_return(*args, **kwargs):
        pass

    monkeypatch.setattr("sqlmodel.Session.exec", mock_exec)
    monkeypatch.setattr("sqlmodel.Session.delete", null_return)
    yield mock_engine
    mock_engine.dispose()


class TestFileRetriever:
    retriever = FakeFileRetriever()

    def test_list_files(self):
        file_list = ListVendorFiles.execute(dir="foo", retriever=self.retriever)
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_load_file(self):
        file = DownloadRemoteFile.execute(
            name="foo.mrc", dir="foo", retriever=self.retriever
        )
        assert file.file_name == "foo.mrc"
        assert file.content == b""


class TestFileWorkflows:
    @pytest.mark.parametrize("source", ["local", "ftp"])
    def test_upload_files(self, mock_engine, tmp_path, caplog, source):
        file1 = tmp_path / "foo.mrc"
        file1.write_bytes(b"333331234567890")
        path = tmp_path / "temp"
        uow = unit_of_work.SqlModelUnitOfWork(mock_engine)
        storage = file_io.LocalFileStorage(base_path=path)
        UploadFileToWorkflow.execute(
            workflow_id="12345",
            filename="qux.mrc",
            content=b"",
            source=source,
            storage=storage,
            uow=uow,
        )
        assert "File added to workflow 12345: IncomingFile(filename=" in caplog.text
        assert "Local file storage location: " in caplog.text

    def test_delete_file(self, mock_engine_with_files):
        uow = unit_of_work.SqlModelUnitOfWork(mock_engine_with_files)
        files = DeleteFileFromWorkflow.execute(id="1", uow=uow, workflow_id="12345")
        assert len(files) == 1
        assert files[0]["filename"] == "foo.mrc"
