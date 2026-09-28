import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf import (
    file_handling,
    process,
    report_service,
    template_handling,
)
from overload_web.domain.pvf import files, order_templates
from overload_web.main import app
from overload_web.presentation import deps


@pytest.fixture
def processed_records(monkeypatch):
    def fake_response(*args, **kwargs):
        return {"id": "1"}

    monkeypatch.setattr(process.ProcessAcquisitionsRecords, "execute", fake_response)
    monkeypatch.setattr(process.ProcessCatalogingRecords, "execute", fake_response)
    monkeypatch.setattr(process.ProcessSelectionRecords, "execute", fake_response)


@pytest.fixture
def mock_workflow_files(monkeypatch):
    def fake_response(*args, **kwargs):
        response = {
            "filename": kwargs.get("filename"),
            "reference": "bar",
            "workflow_id": 1,
            "source": kwargs.get("source"),
        }
        return [response]

    def file_list(*args, **kwargs):
        return ["foo.mrc"]

    def delete_file(*args, **kwargs):
        return []

    def load_file(*args, **kwargs):
        return files.VendorFile(content=b"", file_name=kwargs.get("name"))

    monkeypatch.setattr(file_handling.UploadFileToWorkflow, "execute", fake_response)
    monkeypatch.setattr(file_handling.ListVendorFiles, "execute", file_list)
    monkeypatch.setattr(file_handling.LoadVendorFile, "execute", load_file)
    monkeypatch.setattr(file_handling.DeleteFileFromWorkflow, "execute", delete_file)


@pytest.fixture
def fake_reporter(monkeypatch):
    report_data = {
        "total_records": 1,
        "file_names": ["foo.mrc"],
        "total_files": 1,
        "vendor_report": {},
        "dupes_report": {},
        "missing_barcodes": [],
        "processing_integrity": True,
        "call_no_report": {},
    }

    def null_response(*args, **kwargs):
        return None

    def create_report(*args, **kwrags):
        return report_data

    def report_stats(*arsg, **kwargs):
        return [report_data]

    monkeypatch.setattr(report_service.WriteOutputReport, "execute", null_response)
    monkeypatch.setattr(report_service.CreatePVFOutputReport, "execute", create_report)
    monkeypatch.setattr(report_service.GetDetailedReportData, "execute", report_stats)


@pytest.fixture
def fake_reporter_no_response(monkeypatch):
    def null_response(*args, **kwargs):
        return {}

    monkeypatch.setattr(report_service.CreatePVFOutputReport, "execute", null_response)
    monkeypatch.setattr(report_service.GetDetailedReportData, "execute", null_response)


@pytest.fixture
def fake_template_handler(monkeypatch):
    template = order_templates.OrderTemplate(
        name="foo", agent="bar", primary_matchpoint="isbn", id=1
    )

    def get_template(*args, **kwargs):
        return template

    def list_templates(*args, **kwargs):
        return [template]

    def update_template(*args, **kwargs):
        data_dict = kwargs.get("obj").__dict__
        data_dict.update({"id": 1, "name": "foo"})
        return order_templates.OrderTemplate(**data_dict)

    monkeypatch.setattr(template_handling.SaveNewOrderTemplate, "execute", get_template)
    monkeypatch.setattr(template_handling.GetOrderTemplate, "execute", get_template)
    monkeypatch.setattr(template_handling.ListOrderTemplates, "execute", list_templates)
    monkeypatch.setattr(
        template_handling.UpdateOrderTemplate, "execute", update_template
    )


@pytest.fixture
def fake_template_handler_no_recs(monkeypatch):
    def null_response(*args, **kwargs):
        return None

    monkeypatch.setattr(template_handling.UpdateOrderTemplate, "execute", null_response)


def fake_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


class FakeFetcher:
    def _get_credentials(self) -> str:
        return "creds"


class FakeFTPClient:
    def __init__(self) -> None:
        self.name = "foo"


class FakeFileRetriever:
    def __init__(self) -> None:
        self.client = FakeFTPClient()


def test_api_startup(monkeypatch):
    def fake_engine(*args, **kwargs):
        return create_engine("sqlite:///:memory:")

    monkeypatch.setattr(deps, "create_engine", fake_engine)

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200


class TestApp:
    client = TestClient(app)
    app.dependency_overrides[deps.get_engine] = fake_engine
    app.dependency_overrides[deps.remote_file_retriever] = FakeFileRetriever
    app.dependency_overrides[deps.get_fetcher] = FakeFetcher

    base_url = client.base_url

    def test_files_router_list_remote_files_get(self, mock_workflow_files):
        response = self.client.get("/files/remote/list?vendor=foo")
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remote/list?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(
            ["files", "request", "vendor"]
        )
        assert response.context["files"] == ["foo.mrc"]

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_files_select_ftp_file(self, record_type, mock_workflow_files):
        response = self.client.post(
            "/files/remote/select?vendor=foo",
            data={
                "remote_file": "bar.mrc",
                "workflow_id": 1,
                "record_type": record_type,
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remote/select?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(["files", "request"])
        assert len(response.context["files"]) == 1
        assert response.context["files"][0]["filename"] == "bar.mrc"
        assert response.context["files"][0]["source"] == "ftp"

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_files_upload_file(self, record_type, mock_workflow_files):
        response = self.client.post(
            "/files/upload",
            data={"workflow_id": 1, "vendor": None, "record_type": record_type},
            files={"file": ("baz.mrc", b"", "text/plain")},
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/upload"
        assert sorted(list(response.context.keys())) == sorted(["files", "request"])
        assert len(response.context["files"]) == 1
        assert response.context["files"][0]["filename"] == "baz.mrc"
        assert response.context["files"][0]["source"] == "local"

    def test_files_remove_file(self, mock_workflow_files):
        response = self.client.post(
            "/files/remove", data={"workflow_id": 1, "file_id": 1}
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remove"
        assert sorted(list(response.context.keys())) == sorted(["files", "request"])
        assert response.context["files"] == []

    def test_frontend_root_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Overload Web" in response.text

    def test_frontend_vendor_file_page_get(self):
        response = self.client.get("/process")
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert response.url == f"{self.base_url}/process"
        assert response.context["page_title"] == "Process Vendor File"

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    @pytest.mark.parametrize("workflow", ["pvf", "wc2s"])
    def test_frontend_get_context_update_library(self, library, workflow):
        response = self.client.get(
            f"/update-context?workflow={workflow}&library={library}"
        )
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "collection",
            "collection_disabled",
            "library",
            "record_type",
            "request",
            "template_form_enabled",
        ]

    @pytest.mark.parametrize("collection", ["BL", "RL", ""])
    @pytest.mark.parametrize("workflow", ["pvf", "wc2s"])
    def test_frontend_get_context_update_collection(self, collection, workflow):
        response = self.client.get(
            f"/update-context?workflow={workflow}&collection={collection}"
        )
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "collection",
            "collection_disabled",
            "library",
            "record_type",
            "request",
            "template_form_enabled",
        ]

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    @pytest.mark.parametrize("workflow", ["pvf", "wc2s"])
    def test_frontend_get_context_update_record_type(self, record_type, workflow):
        response = self.client.get(
            f"/update-context?workflow={workflow}&record_type={record_type}"
        )
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "collection",
            "collection_disabled",
            "library",
            "record_type",
            "request",
            "template_form_enabled",
        ]

    def test_frontend_wc2sierra_page_get(self):
        response = self.client.get("/wc2sierra")
        assert response.status_code == 200
        assert "WorldCat2Sierra" in response.text
        assert response.url == f"{self.base_url}/wc2sierra"
        assert response.context["page_title"] == "WorldCat2Sierra"

    def test_ot_router_get_template_form(self, fake_template_handler):
        response = self.client.get("/ot/forms/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request"]

    def test_ot_router_create_template(self, stub_template_data, fake_template_handler):
        response = self.client.post("/ot/template", data=stub_template_data)
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]
        assert response.context["template"].get("id") == 1

    def test_ot_router_get_template(self, fake_template_handler):
        response = self.client.get("/ot/template?template_id=1")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]
        assert response.context["template"]["id"] == 1
        assert response.context["template"]["name"] == "foo"
        assert response.context["template"]["agent"] == "bar"
        assert response.context["template"]["primary_matchpoint"] == "isbn"

    def test_ot_router_get_template_list(self, fake_template_handler):
        response = self.client.get("/ot/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "templates"]

    def test_ot_router_update_template(self, fake_template_handler):
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
        assert response.context["template"]["id"] == 1
        assert response.context["template"]["primary_matchpoint"] == "upc"
        assert response.context["template"]["lang"] == "rus"
        assert response.context["template"]["name"] == "foo"
        assert response.context["template"]["agent"] == "bar"

    def test_ot_router_update_template_not_found(self, fake_template_handler_no_recs):
        response = self.client.patch(
            "/ot/template", data={"primary_matchpoint": "upc", "template_id": 3}
        )
        assert response.status_code == 200
        assert response.context["template"] == {}

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
        self, library, collection, record_type, processed_records
    ):
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "INGRAM",
            "primary_matchpoint": "isbn",
            "name": "foo",
            "agent": "bar",
            "id": 1,
            "workflow_id": "1234",
        }
        response = self.client.post(
            f"/pvf/{record_type}/process-vendor-file", data=context
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "", "cat")],
    )
    def test_pvf_router_process_full_records(
        self, library, collection, record_type, processed_records
    ):
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "workflow_id": "1234",
        }
        response = self.client.post("/pvf/cat/process-vendor-file", data=context)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, record_type", [("nypl", "acq"), ("nypl", "cat"), ("nypl", "sel")]
    )
    def test_pvf_router_process_nypl_collection_error(self, library, record_type):
        """Tests incorrect collection passed to `ProcessingContext` called in `deps.py`"""
        context = {
            "library": library,
            "collection": "",
            "record_type": record_type,
            "vendor": "FOO",
            "workflow_id": "1234",
        }
        with pytest.raises(ValidationError) as exc:
            self.client.post(f"/pvf/{record_type}/process-vendor-file", data=context)
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Collection is required for NYPL records."
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("bpl", "BL", "acq"), ("bpl", "BL", "cat"), ("bpl", "BL", "sel")],
    )
    def test_pvf_router_process_bpl_collection_error(
        self, library, collection, record_type
    ):
        """Tests incorrect collection passed to `ProcessingContext` called in `deps.py`"""
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "FOO",
            "workflow_id": "1234",
        }
        with pytest.raises(ValidationError) as exc:
            self.client.post(f"/pvf/{record_type}/process-vendor-file", data=context)
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Collection should be `None` for BPL records."
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_output_report(self, record_type, fake_reporter):
        response = self.client.get(
            f"/reports/summary?batch_id=1&record_type={record_type}"
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_get_output_report_no_data(
        self, record_type, fake_reporter_no_response
    ):
        response = self.client.get(
            f"/reports/summary?batch_id=10&record_type={record_type}"
        )
        assert response.status_code == 200
        assert '<th scope="row">' not in response.text

    def test_reports_router_get_detailed_report(self, fake_reporter):
        response = self.client.get("/reports/detailed?batch_id=1")
        assert response.status_code == 200

    def test_reports_router_get_detailed_report_no_data(
        self, fake_reporter_no_response
    ):
        response = self.client.get("/reports/detailed?batch_id=10")
        assert response.status_code == 200
        assert '<th scope="row">' not in response.text

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_write_report_to_google_sheet(
        self, record_type, fake_reporter
    ):
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
