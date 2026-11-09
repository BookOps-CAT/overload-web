"""File I/O integration tests."""

from __future__ import annotations

import pytest

from overload_web.application.pvf.file_handling import (
    DownloadVendorFile,
    ListVendorFiles,
)
from overload_web.domain.pvf import commands


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
        file = DownloadVendorFile.execute(
            name="foo.mrc", dir="foo", retriever=FakeFileRetriever()
        )
        assert file.file_name == "foo.mrc"
        assert file.content == b""


class TestFileIOHandlers:
    @pytest.mark.parametrize("source", ["local", "ftp"])
    def test_upload_file_to_workflow(self, stub_order_level_manager, source, caplog):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.UploadFileToWorkflow(
                workflow_id="12345", filename="foo.mrc", content=b"", source=source
            )
        )
        assert len(caplog.records) == 2
        assert "Handling command: UploadFileToWorkflow" == caplog.records[0].msg
        assert caplog.records[1].msg.startswith(
            "File added to workflow 12345: IncomingFile(filename='foo.mrc'"
        )

    def test_delete_file_from_workflow(self, stub_order_level_manager, caplog):
        bus = stub_order_level_manager.bus
        bus.send(commands.DeleteFileFromWorkflow(workflow_id="12345", file_id=1))
        assert len(caplog.records) == 2
        assert "Handling command: DeleteFileFromWorkflow" == caplog.records[0].msg
        assert "File removed from workflow 12345: 1." == caplog.records[1].msg
