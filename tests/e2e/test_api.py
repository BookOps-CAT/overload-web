import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from overload_web.main import app
from overload_web.presentation.api.overload_api import api_router
from overload_web.presentation.frontend.jinja_frontend import frontend_router


class TestApp:
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

    def test_get_context_options(self):
        response = self.client.get("/options/context")
        assert response.status_code == 200
        assert list(response.json().keys()) == ["context"]
        assert sorted(list(response.json()["context"].keys())) == [
            "collection",
            "library",
            "record_type",
            "vendor",
        ]

    def test_get_template_input_options(self):
        response = self.client.get("/options/template")
        assert response.status_code == 200
        assert list(response.json().keys()) == ["field_constants"]

    def test_list_remote_files_get(self, mock_file_service_response):
        response = self.client.get("/list-remote?vendor=foo&dir=bar")
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/list-remote?vendor=foo&dir=bar"
        assert sorted(list(response.json().keys())) == sorted(
            ["files", "directory", "vendor"]
        )
        assert response.json() == {
            "files": ["foo.mrc"],
            "directory": "bar",
            "vendor": "foo",
        }

    def test_load_remote_files_get(self, mock_file_service_response):
        response = self.client.get(
            "/load-remote?vendor=foo&file=bar.mrc&file=baz.mrc&dir=spam"
        )
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/load-remote?vendor=foo&file=bar.mrc&file=baz.mrc&dir=spam"
        )
        assert sorted(list(response.json()[0].keys())) == sorted(
            ["id", "file_name", "content"]
        )

    @pytest.mark.parametrize("library", ["nypl", "bpl"])
    def test_load_local_files_post(self, mock_file_service_response, marc_file_input):
        response = self.client.post(
            "/load-local",
            files=marc_file_input,
        )
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/load-local"
        assert sorted(list(response.json()[0].keys())) == sorted(
            ["id", "file_name", "content"]
        )

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_process_vendor_file_post(self, stub_binary_marc, library, collection):
        context = {
            "context": {
                "library": library,
                "collection": collection,
                "vendor": "BT ROMANCE",
            },
            "records": [
                {
                    "id": {"value": "1"},
                    "file_name": "foo.mrc",
                    "content": stub_binary_marc.read().decode("utf-8"),
                }
            ],
        }
        response = self.client.post("/process/full", json=context)
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/process/full"
        assert isinstance(response.content, bytes)
        assert "b123456789" in response.text
        assert "333331234567890" in response.text
        assert "9781234567890" in response.text

    @pytest.mark.parametrize(
        "library, collection", [("foo", "branches"), ("bar", "research")]
    )
    def test_process_vendor_file_post_invalid_config(
        self, stub_binary_marc, library, collection
    ):
        context = {
            "context": {
                "library": library,
                "collection": collection,
                "vendor": "BT ROMANCE",
            },
            "records": [
                {
                    "id": {"value": "1"},
                    "file_name": "foo.mrc",
                    "content": stub_binary_marc.read().decode("utf-8"),
                }
            ],
        }
        with pytest.raises(RequestValidationError) as exc:
            self.client.post("/process/full", json=context)
        assert "Input should be 'bpl' or 'nypl'" in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_process_vendor_file_order_level_post(
        self, stub_binary_marc, template_data, library, collection
    ):
        context = {
            "context": {
                "library": library,
                "collection": collection,
                "vendor": "BT ROMANCE",
            },
            "records": [
                {
                    "id": {"value": "1"},
                    "file_name": "foo.mrc",
                    "content": stub_binary_marc.read().decode("utf-8"),
                }
            ],
            "template_data": template_data,
        }
        response = self.client.post("/process/order_level", json=context)
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/process/order_level"
        assert isinstance(response.content, bytes)
        assert "b123456789" in response.text
        assert "333331234567890" in response.text
        assert "9781234567890" in response.text

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_process_vendor_file_order_level_other_vendor_post(
        self, stub_binary_marc, template_data, library, collection
    ):
        context = {
            "context": {
                "library": library,
                "collection": collection,
            },
            "records": [
                {
                    "id": {"value": "1"},
                    "file_name": "foo.mrc",
                    "content": stub_binary_marc.read().decode("utf-8"),
                }
            ],
            "template_data": template_data,
        }
        response = self.client.post("/process/order_level", json=context)
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/process/order_level"
        assert isinstance(response.content, bytes)
        assert "b123456789" in response.text
        assert "333331234567890" in response.text
        assert "9781234567890" in response.text

    def test_write_local_file_post(self, mock_file_service_response):
        response = self.client.post(
            "/write-local?dir=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/write-local?dir=foo"

    def test_write_remote_file_post(self, mock_file_service_response):
        response = self.client.post(
            "/write-remote?dir=foo&vendor=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/write-remote?dir=foo&vendor=foo"


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
