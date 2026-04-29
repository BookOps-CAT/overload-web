import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.commands.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.infrastructure import batch_db, clients, template_db
from overload_web.main import app
from overload_web.presentation import deps


@pytest.fixture
def processed_records(monkeypatch, stub_report):
    def fake_response(*args, **kwargs):
        return {"id": "1"}

    monkeypatch.setattr(ProcessAcquisitionsRecords, "execute", fake_response)
    monkeypatch.setattr(ProcessCatalogingRecords, "execute", fake_response)
    monkeypatch.setattr(ProcessSelectionRecords, "execute", fake_response)


def fake_sql_session():
    template = template_db.TemplateModel(
        name="foo", agent="bar", primary_matchpoint="isbn"
    )
    batch = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="foo.mrc", records=b"")],
        report=batch_db.PVFReportModel(
            id=1,
            action=["insert"],
            call_number=["Foo"],
            call_number_match=[True],
            duplicate_records=[[]],
            file_names=["foo.mrc"],
            mixed=[[]],
            other=[[]],
            resource_id=["12345"],
            target_bib_id=["23456"],
            target_call_no=["Foo"],
            target_title=[],
            total_files=1,
            total_records=1,
            updated_by_vendor=[False],
            vendor=["UNKNOWN"],
            missing_barcodes=[],
            processing_integrity=True,
        ),
    )
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        session.add(template)
        session.add(batch)
        session.commit()
        yield session
    session.close()
    test_engine.dispose()


def test_api_startup(monkeypatch):
    def fake_engine(*args, **kwargs):
        return create_engine("sqlite:///:memory:")

    monkeypatch.setattr(deps, "create_engine", fake_engine)

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200


def test_deps():
    engine = create_engine("sqlite:///:memory:")
    deps.create_db_and_tables(engine)
    session = deps.get_session(engine)
    assert isinstance(next(session), Session)
    session.close()
    engine.dispose()


@pytest.mark.usefixtures("mock_session", "mock_sftp_client")
class TestApp:
    client = TestClient(app)
    app.dependency_overrides[deps.get_session] = fake_sql_session
    base_url = client.base_url

    def test_files_router_list_remote_files_get(self):
        response = self.client.get("/files/remote?vendor=foo")
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/files/remote?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(
            ["files", "request", "vendor"]
        )
        assert response.context["files"] == ["foo.mrc"]

    def test_frontend_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "vendor_file_page" in route_names

    def test_frontend_home_get(self):
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
    def test_frontend_get_library_context_update(self, library):
        response = self.client.get(f"/forms/update-library?library={library}")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "disabled",
            "library",
            "request",
        ]

    @pytest.mark.parametrize("collection", ["BL", "RL", "NONE"])
    def test_frontend_get_collection_context_update(self, collection):
        response = self.client.get(f"/forms/update-collection?collection={collection}")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["collection", "request"]

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_frontend_get_record_type_context_update(self, record_type):
        response = self.client.get(
            f"/forms/update-record-type?record_type={record_type}"
        )
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["record_type", "request"]

    def test_ot_router_get_template_form(self):
        response = self.client.get("/ot/forms/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request"]

    def test_ot_router_create_template(self, fake_template_data):
        response = self.client.post("/ot/template", data=fake_template_data)
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]
        assert response.context["template"].get("id") == 2

    def test_ot_router_get_template(self):
        response = self.client.get("/ot/template?template_id=1")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]
        assert response.context["template"]["id"] == 1
        assert response.context["template"]["name"] == "foo"
        assert response.context["template"]["agent"] == "bar"
        assert response.context["template"]["primary_matchpoint"] == "isbn"

    def test_ot_router_get_template_list(self):
        response = self.client.get("/ot/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "templates"]

    def test_ot_router_update_template(self):
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

    def test_ot_router_update_template_not_found(self):
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

    def test_pvf_router_process_full_records_fetcher_error(self):
        """Tests incorrect library passed to `FetcherFactory` called in `deps.py`"""
        context = {
            "library": "Foo",
            "collection": "BL",
            "record_type": "cat",
            "vendor": "FOO",
            "workflow_id": "1234",
        }
        with pytest.raises(ValueError) as exc:
            self.client.post("/pvf/cat/process-vendor-file", data=context)
        assert str(exc.value) == "Invalid library: Foo. Must be 'bpl' or 'nypl'"

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

    @pytest.mark.parametrize("record_type", ["acq", "sel"])
    def test_pvf_router_process_order_records_fetcher_error(self, record_type):
        """Tests incorrect library passed to `FetcherFactory` called in `deps.py`"""
        context = {
            "library": "Foo",
            "collection": "BL",
            "record_type": record_type,
            "vendor": "FOO",
            "primary_matchpoint": "isbn",
            "name": "foo",
            "agent": "bar",
            "id": 1,
            "workflow_id": "1234",
        }

        with pytest.raises(ValueError) as exc:
            self.client.post(f"/pvf/{record_type}/process-vendor-file", data=context)
        assert str(exc.value) == "Invalid library: Foo. Must be 'bpl' or 'nypl'"

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat")],
    )
    def test_pvf_router_process_full_records_platform_error(
        self, library, collection, record_type, mock_nypl_session_error
    ):
        """Tests `FetcherFactory` called in `deps.py`"""
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "FOO",
            "workflow_id": "1234",
        }

        with pytest.raises(clients.BookopsPlatformError) as exc:
            self.client.post("/pvf/cat/process-vendor-file", data=context)
        assert "Trouble connecting: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "acq"),
            ("nypl", "RL", "acq"),
            ("nypl", "BL", "sel"),
            ("nypl", "RL", "sel"),
        ],
    )
    def test_pvf_router_process_order_records_platform_error(
        self, library, collection, record_type, mock_nypl_session_error
    ):
        """Tests `FetcherFactory` called in `deps.py`"""
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "FOO",
            "primary_matchpoint": "isbn",
            "name": "foo",
            "agent": "bar",
            "id": 1,
            "workflow_id": "1234",
        }
        with pytest.raises(clients.BookopsPlatformError) as exc:
            self.client.post(f"/pvf/{record_type}/process-vendor-file", data=context)
        assert "Trouble connecting: " in str(exc.value)

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_output_report(self, record_type):
        response = self.client.get(
            f"/reports/summary?batch_id=1&record_type={record_type}"
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_get_output_report_no_data(self, record_type):
        response = self.client.get(
            f"/reports/summary?batch_id=10&record_type={record_type}"
        )
        assert response.status_code == 200
        assert '<th scope="row">' not in response.text

    def test_reports_router_get_detailed_report(self):
        response = self.client.get("/reports/detailed?batch_id=1")
        assert response.status_code == 200

    def test_reports_router_get_detailed_report_no_data(self):
        response = self.client.get("/reports/detailed?batch_id=10")
        assert response.status_code == 200
        assert '<th scope="row">' not in response.text

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_reports_router_write_report_to_google_sheet(
        self, record_type, mock_sheet_config
    ):
        response = self.client.post(
            "/reports/write?id=1", data={"record_type": record_type}
        )
        assert response.status_code == 200
