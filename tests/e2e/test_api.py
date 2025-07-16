import pytest
from fastapi.testclient import TestClient

from overload_web.main import app
from overload_web.presentation.api import api_router
from overload_web.presentation.frontend import frontend_router


class TestApp:
    client = TestClient(app)

    def test_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "process_full_records" in route_names
        assert "process_order_records" in route_names
        assert "process_vendor_file" in route_names


@pytest.mark.usefixtures("mock_sierra_response")
class TestBackEndAPIRouter:
    client = TestClient(api_router)

    @pytest.fixture
    def form_input(self, template_data, library, collection) -> dict:
        data = {"library": library, "collection": collection}
        data.update({k: v for k, v in template_data.items() if k != "matchpoints"})
        data.update(
            {
                k: template_data["matchpoints"][k]
                for k in list(template_data["matchpoints"].keys())
            }
        )
        return data

    @pytest.fixture
    def marc_file_input(self, stub_binary_marc) -> dict:
        return {"file": ("marc_file.mrc", stub_binary_marc, "text/plain")}

    def test_root_get(self):
        response = self.client.get("/api/")
        assert response.status_code == 200
        assert response.json() == {"app": "Overload Web"}

    def test_get_context_form(self):
        response = self.client.get("/api/forms/context")
        assert response.status_code == 200
        assert sorted(list(response.context["context_form_fields"].keys())) == [
            "collection",
            "library",
            "record_type",
        ]

    def test_get_template_form(self):
        response = self.client.get("/api/forms/template")
        assert response.status_code == 200
        assert sorted(list(response.context.keys())) == ["field_constants", "request"]

    def test_list_remote_files_get(self, mock_file_service_response):
        response = self.client.get("/api/list-remote-files?vendor=foo")
        assert response.status_code == 200
        assert (
            response.url == f"{self.client.base_url}/api/list-remote-files?vendor=foo"
        )
        assert sorted(list(response.context.keys())) == sorted(
            ["files", "request", "vendor"]
        )
        assert response.context["files"] == ["foo.mrc"]

    # @pytest.mark.parametrize(
    #     "library, collection, record_type",
    #     [
    #         ("nypl", "BL", "full"),
    #         ("nypl", "BL", "order_level"),
    #         ("nypl", "RL", "full"),
    #         ("nypl", "RL", "order_level"),
    #         ("bpl", "NONE", "full"),
    #         ("bpl", "NONE", "order_level"),
    #     ],
    # )
    # def test_process_vendor_file_local(
    #     self,
    #     stub_binary_marc,
    #     library,
    #     collection,
    #     record_type,
    #     mock_file_service_response,
    #     template_data,
    # ):
    #     context = {
    #         "library": library,
    #         "collection": collection,
    #         "source": "local",
    #         "record_type": record_type,
    #         "files": [],
    #     }
    #     context.update({k: v for k, v in template_data.items() if k != "matchpoints"})
    #     context["primary"] = "isbn"
    #     response = self.client.post(
    #         "/api/process-vendor-file",
    #         data=context,
    #         files={"file": ("marc_file.mrc", stub_binary_marc, "text/plain")},
    #     )
    #     assert response.status_code == 200

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
    def test_process_vendor_file_remote(
        self,
        library,
        collection,
        record_type,
        mock_file_service_response,
        form_input,
    ):
        context = {
            "library": library,
            "collection": collection,
            "template_input": form_input,
            "source": "remote",
            "record_type": record_type,
            "vendor": "FOO",
            "files": ["foo.mrc"],
        }
        response = self.client.post("/api/process-vendor-file", data=context)
        assert response.status_code == 200

    def test_write_local_file_post(self, mock_file_service_response):
        response = self.client.post(
            "/api/write-local?dir=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/api/write-local?dir=foo"

    def test_write_remote_file_post(self, mock_file_service_response):
        response = self.client.post(
            "/api/write-remote?dir=foo&vendor=foo",
            json={
                "id": {"value": "1"},
                "file_name": "foo.mrc",
                "content": b"".decode("utf-8"),
            },
        )
        assert response.status_code == 200
        assert (
            response.url
            == f"{self.client.base_url}/api/write-remote?dir=foo&vendor=foo"
        )


class TestFrontendRouter:
    client = TestClient(frontend_router)

    def test_home_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Overload Web" in response.text

    def test_vendor_file_page_get(self):
        response = self.client.get("/process")
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert response.url == f"{self.client.base_url}/process"
        assert response.context["page_title"] == "Process Vendor File"
        assert {"name": "Fund", "id": "fund"} in response.context["field_constants"][
            "fixed_fields"
        ]

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
            == f"{self.client.base_url}/process/{record_type}?library=nypl&collection={collection}"
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
            == f"{self.client.base_url}/process/{record_type}?library=bpl&collection="
        )

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "branches"), ("nypl", "research"), ("bpl", None)],
    )
    def test_process_full_records_get(self, library, collection):
        response = self.client.get(
            f"/process/full?library={library}&collection={collection}&vendor=UNKNOWN"
        )
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert (
            response.url
            == f"{self.client.base_url}/process/full?library={library}&collection={collection}&vendor=UNKNOWN"
        )
        assert response.context["page_title"] == "Process Vendor File"
        assert {"name": "Fund", "id": "fund"} in response.context["field_constants"][
            "fixed_fields"
        ]
        assert 'hx-get="/api/forms/template"' not in response.content.decode("utf-8")

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "branches"), ("nypl", "research"), ("bpl", None)],
    )
    def test_process_order_records_get(self, library, collection):
        response = self.client.get(
            f"/process/order-level?library={library}&collection={collection}"
        )
        assert response.status_code == 200
        assert "Process Vendor File" in response.text
        assert (
            response.url
            == f"{self.client.base_url}/process/order-level?library={library}&collection={collection}"
        )
        assert response.context["page_title"] == "Process Vendor File"
        assert {"name": "Fund", "id": "fund"} in response.context["field_constants"][
            "fixed_fields"
        ]
        assert 'hx-get="/api/forms/template"' in response.content.decode("utf-8")
