import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import create_engine

from overload_web.application.pvf import (
    file_handling,
    process_manager,
    report_service,
    template_handling,
)
from overload_web.domain.pvf import files
from overload_web.infrastructure import tables
from overload_web.main import app


class FakeFetcher:
    def _get_credentials(self) -> str:
        return "creds"


class FakeFTPClient:
    def __init__(self) -> None:
        self.name = "foo"


class FakeFileRetriever:
    def __init__(self) -> None:
        self.client = FakeFTPClient()


class FakeFileStorage:
    def __init__(self) -> None:
        self.base_path = "temp/uploads"

    def save(self):
        return "foo"

    def load(self):
        return b"foo"


@pytest.fixture
def overrides(monkeypatch):
    def fetcher(*args, **kwargs):
        return FakeFetcher()

    def retriever(*args, **kwargs):
        return FakeFileRetriever()

    def storage(*args, **kwargs):
        return FakeFileStorage()

    monkeypatch.setattr(
        "overload_web.infrastructure.sierra_clients.FetcherFactory.make", fetcher
    )
    monkeypatch.setattr(
        "overload_web.infrastructure.file_io.SFTPFileRetriever.create_retriever_for_vendor",
        retriever,
    )
    monkeypatch.setattr("overload_web.infrastructure.file_io.LocalFileStorage", storage)


@pytest.mark.usefixtures("overrides")
class TestApp:
    client = TestClient(app)
    # app.dependency_overrides[pvf_deps.get_engine] = mock_engine
    # app.dependency_overrides[pvf_deps.remote_file_retriever] = FakeFileRetriever
    # app.dependency_overrides[pvf_deps.get_fetcher] = FakeFetcher
    # app.dependency_overrides[pvf_deps.local_file_storage] = FakeFileStorage
    app.state.workflow_id = 1
    app.state.engine = create_engine("sqlite:///:memory:")
    base_url = client.base_url

    def test_files_router_list_remote_files_get(self, mocker):
        files = mocker.Mock(return_value=["foo.mrc"])
        mocker.patch.object(file_handling.ListVendorFiles, "execute", files)
        response = self.client.get("/files/remote/list?vendor=foo")
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remote/list?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(
            ["files", "request", "vendor"]
        )
        assert response.context["files"] == ["foo.mrc"]

    def test_files_router_select_ftp_file(self, mocker):
        download = mocker.Mock(
            return_value=files.VendorFile(content=b"", file_name="bar.mrc")
        )
        upload = mocker.Mock(
            return_value=[
                {
                    "filename": "bar.mrc",
                    "reference": "bar",
                    "workflow_id": 1,
                    "source": "ftp",
                }
            ]
        )
        mocker.patch.object(file_handling.DownloadRemoteFile, "execute", download)
        mocker.patch.object(file_handling.UploadFileToWorkflow, "execute", upload)
        response = self.client.post(
            "/files/remote/select?vendor=foo", data={"remote_file": "bar.mrc"}
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remote/select?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(["files", "request"])
        assert len(response.context["files"]) == 1
        assert response.context["files"][0]["filename"] == "bar.mrc"
        assert response.context["files"][0]["source"] == "ftp"

    def test_files_router_upload_file(self, mocker):
        file = {
            "filename": "baz.mrc",
            "reference": "baz",
            "workflow_id": 1,
            "source": "local",
        }
        upload = mocker.Mock(return_value=[file])
        mocker.patch.object(file_handling.UploadFileToWorkflow, "execute", upload)
        response = self.client.post(
            "/files/upload",
            data={"vendor": None},
            files={"file": ("baz.mrc", b"", "text/plain")},
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/upload"
        assert sorted(list(response.context.keys())) == sorted(["files", "request"])
        assert len(response.context["files"]) == 1
        assert response.context["files"][0]["filename"] == "baz.mrc"
        assert response.context["files"][0]["source"] == "local"

    def test_files_router_remove_file(self, mocker):
        file = {
            "filename": "baz.mrc",
            "reference": "baz",
            "workflow_id": 1,
            "source": "local",
        }
        upload = mocker.Mock(return_value=[file])
        mocker.patch.object(file_handling.DeleteFileFromWorkflow, "execute", upload)
        response = self.client.post("/files/remove", data={"file_id": 1})
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remove"
        assert sorted(list(response.context.keys())) == sorted(["files", "request"])
        assert len(response.context["files"]) == 1

    def test_frontend_router_root_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Overload Web" in response.text

    def test_frontend_router_vendor_file_page_get(self):
        response = self.client.get("/process")
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert response.url == f"{self.base_url}/process"
        assert response.context["page_title"] == "Process Vendor File"

    @pytest.mark.parametrize(
        "library, collection, record_type, workflow, collection_disabled, template_enabled",
        [
            ("nypl", "BL", "acq", "pvf", False, True),
            ("nypl", "RL", "cat", "wc2s", False, False),
            ("nypl", "", "cat", "pvf", False, False),
            ("bpl", "", "sel", "wc2s", True, True),
        ],
    )
    def test_frontend_router_get_context_update(
        self,
        library,
        collection,
        workflow,
        record_type,
        collection_disabled,
        template_enabled,
    ):
        response = self.client.get(
            f"/update-context?workflow={workflow}&library={library}&collection={collection}&record_type={record_type}"
        )
        assert response.status_code == 200
        assert response.context["library"] == library
        assert response.context["collection"] == collection
        assert response.context["record_type"] == record_type
        assert response.context["collection_disabled"] == collection_disabled
        assert response.context["template_form_enabled"] == template_enabled

    def test_frontend_router_wc2sierra_page_get(self):
        response = self.client.get("/wc2sierra")
        assert response.status_code == 200
        assert "WorldCat2Sierra" in response.text
        assert response.url == f"{self.base_url}/wc2sierra"
        assert response.context["page_title"] == "WorldCat2Sierra"

    def test_ot_router_get_template_form(self):
        response = self.client.get("/ot/forms/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request"]

    def test_ot_router_create_template(self, mocker):
        template = mocker.Mock()
        mocker.patch.object(template_handling.SaveNewOrderTemplate, "execute", template)
        response = self.client.post(
            "/ot/template", data={"name": "Foo", "agent": "Bar", "id": 1}
        )
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]

    def test_ot_router_get_template(self, mocker):
        template = mocker.Mock()
        mocker.patch.object(template_handling.GetOrderTemplate, "execute", template)
        response = self.client.get("/ot/template?template_id=1")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]

    def test_ot_router_get_template_list(self, mocker):
        templates = mocker.Mock(return_value=[])
        mocker.patch.object(template_handling.ListOrderTemplates, "execute", templates)
        response = self.client.get("/ot/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "templates"]

    def test_ot_router_update_template(self, mocker):
        template = mocker.Mock()
        mocker.patch.object(template_handling.UpdateOrderTemplate, "execute", template)
        response = self.client.patch(
            "/ot/template",
            data={
                "name": "foo",
                "agent": "bar",
                "primary_matchpoint": "upc",
                "lang": "rus",
                "template_id": 1,
            },
        )
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]

    def test_pvf_router_initialize_workflow(self, mocker, caplog):
        mock_obj = mocker.Mock()
        mocker.patch("overload_web.infrastructure.unit_of_work.Session", mock_obj)
        response = self.client.get("/pvf/workflow")
        assert response.status_code == 200
        assert "Created new workflow ID: " in caplog.text

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "acq"),
            ("nypl", "BL", "sel"),
            ("nypl", "RL", "acq"),
            ("nypl", "RL", "sel"),
            ("bpl", "", "acq"),
            ("bpl", "", "sel"),
        ],
    )
    def test_pvf_router_process_order_records(
        self, library, collection, record_type, mocker
    ):
        mock = mocker.Mock()
        mocker.patch.object(
            process_manager.WorkflowManager, "handle_workflow_started_order_level", mock
        )
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "INGRAM",
            "primary_matchpoint": "isbn",
            "name": "foo",
            "agent": "bar",
            "id": 1,
        }
        response = self.client.post("/pvf/process-order-records", data=context)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "", "cat")],
    )
    def test_pvf_router_process_full_records(
        self, library, collection, record_type, mocker
    ):
        mock = mocker.Mock()
        mocker.patch.object(
            process_manager.WorkflowManager, "handle_workflow_started_full_level", mock
        )
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
        }
        response = self.client.post("/pvf/process-full-records", data=context)
        assert response.status_code == 200

    @pytest.mark.parametrize("library, record_type", [("nypl", "acq"), ("nypl", "sel")])
    def test_pvf_router_process_order_records_nypl_collection_error(
        self, library, record_type
    ):
        """Tests incorrect collection passed to `ProcessingContext` called in `deps.py`"""
        context = {
            "library": library,
            "collection": "",
            "record_type": record_type,
            "vendor": "FOO",
        }
        with pytest.raises(ValidationError) as exc:
            self.client.post("/pvf/process-order-records", data=context)
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Collection is required for NYPL records."
        )

    @pytest.mark.parametrize("library, record_type", [("nypl", "cat")])
    def test_pvf_router_process_full_records_nypl_collection_error(
        self, library, record_type
    ):
        """Tests incorrect collection passed to `ProcessingContext` called in `deps.py`"""
        context = {
            "library": library,
            "collection": "",
            "record_type": record_type,
            "vendor": "FOO",
        }
        with pytest.raises(ValidationError) as exc:
            self.client.post("/pvf/process-full-records", data=context)
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Collection is required for NYPL records."
        )

    @pytest.mark.parametrize(
        "library, collection, record_type", [("bpl", "BL", "acq"), ("bpl", "BL", "sel")]
    )
    def test_pvf_router_process_order_records_bpl_collection_error(
        self, library, collection, record_type
    ):
        """Tests incorrect collection passed to `ProcessingContext` called in `deps.py`"""
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "FOO",
        }
        with pytest.raises(ValidationError) as exc:
            self.client.post("/pvf/process-order-records", data=context)
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Collection should be `None` for BPL records."
        )

    @pytest.mark.parametrize("library, collection, record_type", [("bpl", "BL", "cat")])
    def test_pvf_router_process_full_records_bpl_collection_error(
        self, library, collection, record_type
    ):
        """Tests incorrect collection passed to `ProcessingContext` called in `deps.py`"""
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "FOO",
        }
        with pytest.raises(ValidationError) as exc:
            self.client.post("/pvf/process-full-records", data=context)
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Collection should be `None` for BPL records."
        )

    def test_pvf_router_workflow_status_check_pending(self, mocker, caplog):
        mock_obj = mocker.Mock(
            return_value=tables.WorkflowStateModel(id="123", status="PENDING")
        )
        mocker.patch("overload_web.infrastructure.unit_of_work.Session.get", mock_obj)
        response = self.client.get("/pvf/workflow/123/status")
        assert response.status_code == 200
        assert list(response.context.keys()) == ["workflow_id", "request"]
        assert "Current workflow state: PENDING" in caplog.text

    def test_pvf_router_workflow_status_check_completed(self, mocker, caplog):
        mock_obj = mocker.Mock(
            return_value=tables.WorkflowStateModel(
                id="123", status="COMPLETED", batch_id=1
            )
        )
        mocker.patch("overload_web.infrastructure.unit_of_work.Session.get", mock_obj)
        response = self.client.get("/pvf/workflow/123/status")
        assert response.status_code == 200
        assert list(response.context.keys()) == ["batch_id", "record_type", "request"]
        assert "Current workflow state: COMPLETED" in caplog.text

    def test_pvf_router_workflow_status_check_missing(self, mocker):
        mock_obj = mocker.Mock(return_value=None)
        mocker.patch("overload_web.infrastructure.unit_of_work.Session.get", mock_obj)
        response = self.client.get("/pvf/workflow/123/status")
        assert response.status_code == 200
        assert "<div class='error'>Workflow not found.</div>" in response.text

    def test_pvf_router_workflow_status_check_failed(self, mocker):
        mock_obj = mocker.Mock(
            return_value=tables.WorkflowStateModel(
                id="123", status="FAILED", error_message="Workflow failed"
            )
        )
        mocker.patch("overload_web.infrastructure.unit_of_work.Session.get", mock_obj)
        response = self.client.get("/pvf/workflow/123/status")
        assert response.status_code == 200
        assert "<div class='error'>Error: Workflow failed</div>" in response.text

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_output_report(self, record_type, mocker):
        mock_obj = mocker.Mock(return_value={})
        mocker.patch.object(report_service.CreatePVFOutputReport, "execute", mock_obj)
        response = self.client.get(
            f"/reports/summary?batch_id=1&record_type={record_type}"
        )
        assert response.status_code == 200

    def test_reports_router_get_detailed_report(self, mocker):
        mock_obj = mocker.Mock(return_value={})
        mocker.patch.object(report_service.GetDetailedReportData, "execute", mock_obj)
        response = self.client.get("/reports/detailed?batch_id=1")
        assert response.status_code == 200

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_write_report_to_google_sheet(self, record_type, mocker):
        mock = mocker.Mock()
        mocker.patch.object(report_service.WriteOutputReport, "execute", mock)
        response = self.client.post(
            f"/reports/write?batch_id=1&record_type={record_type}"
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "")]
    )
    def test_wc2s_router_match_record(self, library, collection, mock_wc_session):
        context = {
            "library": library,
            "collection": collection,
            "id_type": "isbn",
            "material_type": "print",
            "action": "catalog",
            "record_level": "1",
            "cat_agency": "any",
            "cat_rules": "any",
            "data_source": "id",
        }
        response = self.client.post(
            "/wc2s/match_record",
            data=context,
            files={"file": ("foo.txt", b"9781234567890", "text/plain")},
        )
        context = response.context
        assert response.status_code == 200
        assert len(context["wc2s_results"]) > 0

    def test_api_startup(self, monkeypatch):
        def mock_engine(*args, **kwargs):
            return create_engine("sqlite:///:memory:")

        monkeypatch.setattr(
            "overload_web.presentation.pvf_deps.create_engine", mock_engine
        )

        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
