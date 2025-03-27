import io

import pytest
from fastapi.testclient import TestClient

from overload_web.api.overload_api import api_router
from overload_web.frontend.jinja_frontend import frontend_router
from overload_web.main import app


class TestAPIClient:
    client = TestClient(app)

    def test_root_get(self):
        routes = self.client.app.router.__dict__["routes"]
        route_names = [i.name for i in routes]
        assert "root" in route_names
        assert "vendor_file_process" in route_names
        assert "vendor_file_page" in route_names


class TestAPIRouter:
    client = TestClient(api_router)

    def test_root_get(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"app": "Overload Web"}

    @pytest.mark.parametrize(
        "library, destination",
        [("nypl", "branches"), ("nypl", "research"), ("bpl", None)],
    )
    def test_process_vendor_file_post(
        self, stub_pvf_form_data, stub_bib, stub_sierra_service, library, destination
    ):
        response = self.client.post(
            "/vendor_file",
            files={
                "file": ("marc_file.mrc", io.BytesIO(stub_bib.as_marc()), "text/plain")
            },
            data=stub_pvf_form_data,
        )
        json_response = response.json()
        assert response.status_code == 200
        assert response.url == f"{self.client.base_url}/vendor_file"
        assert isinstance(json_response, list)
        assert sorted(list(response.json()[0].keys())) == sorted(
            ["bib_id", "isbn", "upc", "oclc_number", "orders", "library"]
        )

    @pytest.mark.parametrize(
        "library, destination", [("foo", "branches"), ("bar", "research")]
    )
    def test_process_vendor_file_post_invalid_config(
        self, stub_bib, stub_pvf_form_data, library, destination
    ):
        with pytest.raises(ValueError) as exc:
            self.client.post(
                "/vendor_file",
                files={
                    "file": (
                        "marc_file.mrc",
                        io.BytesIO(stub_bib.as_marc()),
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
