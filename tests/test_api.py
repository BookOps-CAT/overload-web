import io
import json
from fastapi.testclient import TestClient
import pytest
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


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_vendor_file_post(stub_template, stub_order, stub_sierra_service):
    stub_order_file = io.BytesIO(json.dumps(stub_order.__dict__).encode())
    response = client.post(
        "/vendor_file",
        files={"order_file": stub_order_file},
        data=stub_template.__dict__,
    )
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/vendor_file"
    assert "Order File" in response.text
    assert "Enter Template Data" in response.text


@pytest.mark.parametrize("library", ["foo"])
def test_process_vendor_file_post_invalid_config(stub_order, stub_template):
    stub_order_file = io.BytesIO(json.dumps(stub_order.__dict__).encode())
    with pytest.raises(ValueError) as exc:
        client.post(
            "/vendor_file",
            files={"order_file": stub_order_file},
            data=stub_template.__dict__,
        )
    assert "Invalid library. Must be 'bpl' or 'nypl'" in str(exc.value)
