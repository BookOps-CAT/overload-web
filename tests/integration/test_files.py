import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.pvf.file_handling import (
    DeleteFileFromWorkflow,
    ListVendorFiles,
    LoadAllWorkflowFiles,
    LoadVendorFile,
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


class FakeFileRetriever:
    def __init__(self) -> None:
        pass

    def list(self, dir: str) -> list[str]:
        return ["foo.mrc"]

    def download(self, name: str, dir: str) -> bytes:
        return b""


class TestFileRetriever:
    retriever = FakeFileRetriever()

    def test_list_files(self):
        file_list = ListVendorFiles.execute(dir="foo", retriever=self.retriever)
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_load_file(self):
        file = LoadVendorFile.execute(
            name="foo.mrc", dir="foo", retriever=self.retriever
        )
        assert file.file_name == "foo.mrc"
        assert file.content == b""


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
