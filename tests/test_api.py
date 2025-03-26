import pytest
from fastapi.testclient import TestClient

from overload_web.main import app

client = TestClient(app)


def test_root_get():
    response = client.get("/")
    assert response.status_code == 200
    assert "BookOps Cataloging Department browser-based toolbox." in response.text


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_vendor_file_get(stub_sierra_service):
    response = client.get("/vendor_file")
    assert response.status_code == 200
    assert "Process Vendor File" in response.text
    assert response.url == f"{client.base_url}/vendor_file"
    assert response.context["page_title"] == "Process Vendor File"
    assert {"name": "Fund", "id": "fund"} in response.context["fixed_fields"]
