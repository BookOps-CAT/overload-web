import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from overload_web.main import app
from overload_web.order_templates.infrastructure import tables
from overload_web.presentation import deps, template_service_dep


def stub_sql_session():
    template = tables.TemplateTable(name="foo", agent="bar", primary_matchpoint="isbn")
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        session.add(template)
        session.commit()
        yield session


def test_api_startup(monkeypatch):
    monkeypatch.setattr(deps, "create_db_and_tables", stub_sql_session)

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200


def test_deps():
    deps.create_db_and_tables()
    session = template_service_dep.get_session()
    assert isinstance(next(session), Session)


@pytest.mark.usefixtures("mock_sierra_response", "mock_sftp_client")
class TestApp:
    client = TestClient(app)
    app.dependency_overrides[template_service_dep.get_session] = stub_sql_session
    base_url = client.base_url

    def test_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "process_records_page" in route_names

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
            ("branches", "acq"),
            ("branches", "cat"),
            ("branches", "sel"),
            ("research", "acq"),
            ("research", "cat"),
            ("research", "sel"),
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
        ["acq", "cat", "sel"],
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
            ("nypl", "branches", "cat"),
            ("nypl", "branches", "sel"),
            ("nypl", "branches", "acq"),
            ("nypl", "research", "cat"),
            ("nypl", "research", "sel"),
            ("nypl", "research", "acq"),
            ("bpl", None, "cat"),
            ("bpl", None, "sel"),
            ("bpl", None, "acq"),
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

    def test_api_create_template(self, template_data):
        response = self.client.post("/api/template", data=template_data)
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]
        assert response.context["template"].get("id") == 2

    def test_api_get_template(self):
        response = self.client.get("/api/template?template_id=1")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "template"]
        assert response.context["template"]["id"] == 1
        assert response.context["template"]["name"] == "foo"
        assert response.context["template"]["agent"] == "bar"
        assert response.context["template"]["primary_matchpoint"] == "isbn"

    def test_api_get_template_list(self):
        response = self.client.get("/api/templates")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["request", "templates"]

    def test_api_update_template(self):
        response = self.client.patch(
            "/api/template",
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

    def test_api_update_template_not_found(self):
        response = self.client.patch(
            "/api/template", data={"primary_matchpoint": "upc", "template_id": 3}
        )
        assert response.status_code == 200
        assert response.context["template"] == {}

    def test_api_list_remote_files_get(self):
        response = self.client.get("/api/remote-files?vendor=foo")
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/api/remote-files?vendor=foo"
        assert sorted(list(response.context.keys())) == sorted(
            ["files", "request", "vendor"]
        )
        assert response.context["files"] == ["foo.mrc"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "cat"),
            ("nypl", "BL", "acq"),
            ("nypl", "BL", "sel"),
            ("nypl", "RL", "cat"),
            ("nypl", "RL", "acq"),
            ("nypl", "RL", "sel"),
            ("bpl", "NONE", "cat"),
            ("bpl", "NONE", "acq"),
            ("bpl", "NONE", "sel"),
        ],
    )
    def test_api_process_vendor_file_local(self, library, collection, record_type):
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": None,
            "primary_matchpoint": "isbn",
            "name": "foo",
            "agent": "bar",
            "id": 1,
        }
        files = {"files": ("test.mrc", b"", "application/octet-stream")}
        response = self.client.post(
            "/api/process-vendor-file", data=context, files=files
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "acq"),
            ("nypl", "BL", "cat"),
            ("nypl", "BL", "sel"),
            ("nypl", "RL", "acq"),
            ("nypl", "RL", "cat"),
            ("nypl", "RL", "sel"),
            ("bpl", "NONE", "acq"),
            ("bpl", "NONE", "cat"),
            ("bpl", "NONE", "sel"),
        ],
    )
    def test_api_process_vendor_file_remote(self, library, collection, record_type):
        context = {
            "library": library,
            "collection": collection,
            "record_type": record_type,
            "vendor": "FOO",
            "primary_matchpoint": "isbn",
            "name": "foo",
            "agent": "bar",
            "id": 1,
        }
        files = {"files": (None, "test.mrc")}
        response = self.client.post(
            "/api/process-vendor-file", data=context, files=files
        )
        assert response.status_code == 200

    def test_api_write_local_file_post(self, mocker):
        mock_file = mocker.mock_open(read_data="")
        mocker.patch("builtins.open", mock_file)

        response = self.client.post(
            "/api/local-file?dir=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/api/local-file?dir=foo"

    def test_api_write_remote_file_post(self):
        response = self.client.post(
            "/api/remote-file?dir=foo&vendor=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.base_url}/api/remote-file?dir=foo&vendor=foo"

    def test_htmx_get_local_upload_form(self):
        response = self.client.get("/htmx/forms/local-files")
        assert response.status_code == 200
        assert "Select Files" in response.text
        assert response.url == f"{self.base_url}/htmx/forms/local-files"

    def test_htmx_get_remote_file_form(self):
        response = self.client.get("/htmx/forms/remote-files")
        assert response.status_code == 200
        assert "Select Files" in response.text
        assert response.url == f"{self.base_url}/htmx/forms/remote-files"

    def test_htmx_get_context_form(self):
        response = self.client.get("/htmx/forms/context")
        assert response.status_code == 200
        assert list(response.context.keys()) == ["request"]

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
        assert sorted(list(response.context.keys())) == ["request"]
