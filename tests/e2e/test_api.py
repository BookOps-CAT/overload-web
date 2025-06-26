import pytest
from fastapi.testclient import TestClient

from overload_web.main import app
from overload_web.presentation.api.overload_api import api_router
from overload_web.presentation.frontend.jinja_frontend import frontend_router


class TestFrontEndAPIRouter:
    client = TestClient(app)

    def test_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "vendor_file_process" in route_names
        assert "vendor_file_page" in route_names


@pytest.mark.usefixtures("mock_sierra_response")
class TestBackEndAPIRouter:
    client = TestClient(api_router)

    @pytest.fixture
    def form_input(self, template_data, library, collection) -> dict:
        data = {"library": library, "collection": collection}
        data.update({k: v for k, v in template_data.items() if k != "matchpoints"})
        data.update(
            {
                f"{k}_matchpoint": template_data["matchpoints"][k]
                for k in list(template_data["matchpoints"].keys())
            }
        )
        return data

    @pytest.fixture
    def marc_file_input(self, stub_binary_marc) -> dict:
        return {"file": ("marc_file.mrc", stub_binary_marc, "text/plain")}

    def test_root_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"app": "Overload Web"}

    def test_list_files_get_remote(self, mock_file_service_response):
        response = self.client.get("/list_files?dir=foo&remote=True&vendor=foo")
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/list_files?dir=foo&remote=True&vendor=foo"
        )

    def test_list_files_get_local(self, mock_file_service_response):
        response = self.client.get("/list_files?dir=foo&remote=False&vendor=foo")
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/list_files?dir=foo&remote=False&vendor=foo"
        )

    def test_list_files_get_missing_vendor(self, mock_file_service_response):
        with pytest.raises(ValueError) as exc:
            self.client.get("/list_files?dir=foo&remote=True")
        assert str(exc.value) == "`vendor` arg required for remote files."

    def test_load_files_get_remote(self, mock_file_service_response):
        response = self.client.get(
            "/load_files?file=bar.mrc&file=baz.mrc&dir=foo&remote=True&vendor=foo"
        )
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/load_files?file=bar.mrc&file=baz.mrc&dir=foo&remote=True&vendor=foo"
        )
        assert sorted(list(response.json()[0].keys())) == sorted(
            ["id", "content", "file_name"]
        )

    def test_load_files_get_local(self, mock_file_service_response):
        response = self.client.get(
            "/load_files?file=baz.mrc&dir=foo&remote=False&vendor=foo"
        )
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/load_files?file=baz.mrc&dir=foo&remote=False&vendor=foo"
        )

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "branches"), ("nypl", "research"), ("bpl", None)],
    )
    def test_process_vendor_file_post(
        self, stub_pvf_form_data, stub_binary_marc, library, collection
    ):
        response = self.client.post(
            "/vendor_file",
            files={"file": ("marc_file.mrc", stub_binary_marc, "text/plain")},
            data=stub_pvf_form_data,
        )
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/vendor_file"
        assert isinstance(response.content, bytes)
        assert "b123456789" in response.text
        assert "333331234567890" in response.text
        assert "9781234567890" in response.text

    @pytest.mark.parametrize(
        "library, collection", [("foo", "branches"), ("bar", "research")]
    )
    def test_process_vendor_file_post_invalid_config(
        self, stub_binary_marc, stub_pvf_form_data, library, collection
    ):
        with pytest.raises(ValueError) as exc:
            self.client.post(
                "/vendor_file",
                files={
                    "file": (
                        "marc_file.mrc",
                        stub_binary_marc,
                        "text/plain",
                    )
                },
                data=stub_pvf_form_data,
            )
        assert "not a valid LibrarySystem" in str(exc.value)

    def test_write_file_post_remote(self, mock_file_service_response):
        response = self.client.post(
            "/write_file?dir=foo&remote=True&vendor=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/write_file?dir=foo&remote=True&vendor=foo"
        )

    def test_write_file_post_local(self, mock_file_service_response):
        response = self.client.post(
            "/write_file?dir=foo&remote=False&vendor=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/write_file?dir=foo&remote=False&vendor=foo"
        )


class TestFrontendRouter:
    client = TestClient(frontend_router)

    def test_root_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "BookOps Cataloging Department browser-based toolbox." in response.text
        assert "Overload Web" in response.text

    def test_process_vendor_file_get(self):
        response = self.client.get("/vendor_file")
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert response.url == f"{self.client.base_url}/vendor_file"
        assert response.context["page_title"] == "Process Vendor File"
        assert {"name": "Fund", "id": "fund"} in response.context["field_constants"][
            "fixed_fields"
        ]
