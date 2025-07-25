import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from overload_web.main import app
from overload_web.presentation import dependencies


def stub_sql_session():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session


def test_api_startup(monkeypatch):
    def stub_tables():
        test_engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(test_engine)

    monkeypatch.setattr(dependencies, "create_db_and_tables", stub_tables)

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200


@pytest.mark.usefixtures("mock_sierra_response", "mock_sftp_client")
class TestApp:
    client = TestClient(app)
    app.dependency_overrides[dependencies.get_session] = stub_sql_session
    base_url = client.base_url

    def test_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "process_records" in route_names

    def test_home_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Overload Web" in response.text

    def test_vendor_file_page_get(self):
        response = self.client.get("/process")
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert response.url == f"{self.base_url}/process"
        assert response.context["page_title"] == "Process Vendor File"

    @pytest.mark.parametrize(
        "collection, record_type",
        [
            ("branches", "full"),
            ("research", "full"),
            ("branches", "order-level"),
            ("research", "order-level"),
        ],
    )
    def test_post_context_form_nypl(self, collection, record_type):
        response = self.client.post(
            "/process",
            data={
                "library": "nypl",
                "collection": collection,
                "record_type": record_type,
            },
        )
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert (
            response.url
            == f"{self.base_url}/process/context?library=nypl&collection={collection}&record_type={record_type}"
        )

    @pytest.mark.parametrize(
        "record_type",
        ["full", "order-level"],
    )
    def test_post_context_form_bpl(self, record_type):
        response = self.client.post(
            "/process",
            data={
                "library": "bpl",
                "collection": None,
                "record_type": record_type,
            },
        )
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert (
            response.url
            == f"{self.base_url}/process/context?library=bpl&collection=&record_type={record_type}"
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "branches", "full"),
            ("nypl", "branches", "order_level"),
            ("nypl", "research", "full"),
            ("nypl", "research", "order_level"),
            ("bpl", None, "full"),
            ("bpl", None, "order_level"),
        ],
    )
    def test_process_records_get(self, library, collection, record_type):
        response = self.client.get(
            f"/process/context?library={library}&collection={collection}&record_type={record_type}"
        )
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert (
            response.url
            == f"{self.base_url}/process/context?library={library}&collection={collection}&record_type={record_type}"
        )
        assert response.context["page_title"] == "Process Vendor File"

    def test_api_create_template(self):
        template_data = {"name": "foo", "agent": "bar", "primary_matchpoint": "isbn"}
        response = self.client.post("/api/template", data=template_data)
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "field_constants",
            "request",
            "template",
        ]
        assert response.context["template"].get("id") == 1

    def test_api_get_template(self):
        response = self.client.get("/api/template?template_id=1")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "field_constants",
            "request",
            "template",
        ]
        assert response.context["template"] == {}

    def test_api_get_template_list(self):
        response = self.client.get("/api/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "templates"]

    def test_api_list_remote_files_get(self):
        response = self.client.get("/api/list-remote-files?vendor=foo")
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/api/list-remote-files?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(
            ["files", "request", "vendor"]
        )
        assert response.context["files"] == ["foo.mrc"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "full"),
            ("nypl", "BL", "order_level"),
            ("nypl", "RL", "full"),
            ("nypl", "RL", "order_level"),
            ("bpl", "NONE", "full"),
            ("bpl", "NONE", "order_level"),
        ],
    )
    def test_api_process_vendor_file_local(self, library, collection, record_type):
        context = {
            "library": library,
            "collection": collection,
            "source": "local",
            "record_type": record_type,
            "vendor": None,
            "primary": "isbn",
        }
        files = {"files": ("test.mrc", b"", "application/octet-stream")}
        response = self.client.post(
            "/api/process-vendor-file", data=context, files=files
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "full"),
            ("nypl", "BL", "order_level"),
            ("nypl", "RL", "full"),
            ("nypl", "RL", "order_level"),
            ("bpl", "NONE", "full"),
            ("bpl", "NONE", "order_level"),
        ],
    )
    def test_api_process_vendor_file_remote(
        self, library, collection, record_type, template_data
    ):
        context = {
            "library": library,
            "collection": collection,
            "template_input": template_data,
            "source": "remote",
            "record_type": record_type,
            "vendor": "FOO",
            "files": ["foo.mrc"],
        }
        response = self.client.post("/api/process-vendor-file", data=context)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "full"),
            ("nypl", "BL", "order_level"),
            ("nypl", "RL", "full"),
            ("nypl", "RL", "order_level"),
            ("bpl", "NONE", "full"),
            ("bpl", "NONE", "order_level"),
        ],
    )
    def test_api_process_vendor_file_remote_no_vendor(
        self, library, collection, record_type, template_data
    ):
        context = {
            "library": library,
            "collection": collection,
            "template_input": template_data,
            "source": "remote",
            "record_type": record_type,
            "vendor": None,
            "files": ["foo.mrc"],
        }
        with pytest.raises(ValueError) as exc:
            self.client.post("/api/process-vendor-file", data=context)
        assert str(exc.value) == "Vendor must be provided for remote files"

    def test_api_write_local_file_post(self, mocker):
        mock_file = mocker.mock_open(read_data="")
        mocker.patch("builtins.open", mock_file)

        response = self.client.post(
            "/api/write-local?dir=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/api/write-local?dir=foo"

    def test_api_write_remote_file_post(self):
        response = self.client.post(
            "/api/write-remote?dir=foo&vendor=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/api/write-remote?dir=foo&vendor=foo"

    def test_htmx_get_file_source(self):
        response = self.client.get("/htmx/file-source")
        assert response.status_code == 200
        assert "File Source" in response.text
        assert "Local Upload" in response.text
        assert "Remote Server" in response.text
        assert response.url == f"{self.base_url}/htmx/file-source"

    def test_htmx_get_local_upload_form(self):
        response = self.client.get("htmx/local-file-form")
        assert response.status_code == 200
        assert "Select Files" in response.text
        assert response.url == f"{self.base_url}/htmx/local-file-form"

    def test_htmx_get_remote_file_form(self):
        response = self.client.get("/htmx/remote-file-form")
        assert response.status_code == 200
        assert "Select Files" in response.text
        assert response.url == f"{self.base_url}/htmx/remote-file-form"

    def test_htmx_get_pvf_button(self):
        response = self.client.get("/htmx/pvf-button")
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert response.url == f"{self.base_url}/htmx/pvf-button"

    def test_htmx_get_context_form(self):
        response = self.client.get("/htmx/forms/context")
        assert response.status_code == 200
        assert sorted(list(response.context["context_form_fields"].keys())) == [
            "collection",
            "library",
            "record_type",
        ]

    def test_htmx_template_form_selector(self):
        response = self.client.get("/htmx/apply-template-button")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["field_constants", "request"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "full"),
            ("nypl", "BL", "order_level"),
            ("nypl", "RL", "full"),
            ("nypl", "RL", "order_level"),
            ("bpl", "NONE", "full"),
            ("bpl", "NONE", "order_level"),
        ],
    )
    def test_htmx_get_disabled_context_form(self, library, collection, record_type):
        response = self.client.get(
            f"/htmx/forms/disabled-context?library={library}&collection={collection}&record_type={record_type}"
        )
        assert response.status_code == 200
        assert sorted(list(response.context["context"].keys())) == [
            "collection",
            "library",
            "record_type",
        ]

    def test_htmx_get_template_form(self):
        response = self.client.get("/htmx/forms/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == [
            "field_constants",
            "request",
            "template",
        ]
