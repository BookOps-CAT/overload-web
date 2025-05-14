import pytest
from fastapi.testclient import TestClient

from overload_web.main import app
from overload_web.presentation.api.overload_api import api_router
from overload_web.presentation.frontend.jinja_frontend import frontend_router


class TestAPIClient:
    client = TestClient(app)

    def test_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "vendor_file_process" in route_names
        assert "vendor_file_page" in route_names


@pytest.mark.usefixtures("mock_sierra_response")
class TestAPIRouter:
    client = TestClient(api_router)

    def test_root_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"app": "Overload Web"}

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
        assert "Invalid library. Must be 'bpl' or 'nypl'" in str(exc.value)


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
