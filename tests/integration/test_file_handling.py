from __future__ import annotations

import pytest

from overload_web.application.pvf.file_handling import (
    DeleteFileFromWorkflow,
    DownloadRemoteFile,
    ListVendorFiles,
    UploadFileToWorkflow,
)
from overload_web.infrastructure import file_io


class FakeFileRetriever:
    def __init__(self) -> None:
        pass

    def list(self, dir: str) -> list[str]:
        return ["foo.mrc"]

    def download(self, name: str, dir: str) -> bytes:
        return b""


class TestFileHandling:
    def test_list_vendor_files(self):
        file_list = ListVendorFiles.execute(dir="foo", retriever=FakeFileRetriever())
        assert len(file_list) == 1
        assert file_list[0] == "foo.mrc"

    def test_download_remote_file(self):
        file = DownloadRemoteFile.execute(
            name="foo.mrc", dir="foo", retriever=FakeFileRetriever()
        )
        assert file.file_name == "foo.mrc"
        assert file.content == b""

    @pytest.mark.parametrize("source", ["local", "ftp"])
    def test_upload_file_to_workflow(self, fake_uow, tmp_path, caplog, source):
        file1 = tmp_path / "foo.mrc"
        file1.write_bytes(b"333331234567890")
        path = tmp_path / "temp"
        storage = file_io.LocalFileStorage(base_path=path)
        UploadFileToWorkflow.execute(
            workflow_id="12345",
            filename="qux.mrc",
            content=b"",
            source=source,
            storage=storage,
            uow=fake_uow,
        )
        assert "File added to workflow 12345: IncomingFile(filename=" in caplog.text
        assert "Local file storage location: " in caplog.text

    def test_delete_file_from_workflow(self, fake_uow):
        files = DeleteFileFromWorkflow.execute(
            id="1", uow=fake_uow, workflow_id="12345"
        )
        assert len(files) == 1
        assert files[0]["filename"] == "foo.mrc"
