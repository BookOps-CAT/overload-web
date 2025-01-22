import io
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
    assert {"name": "Fund", "id": "fund"} in response.context["field_constants"][
        "fixed_fields"
    ]


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_vendor_file_post(
    stub_template, stub_bib, stub_sierra_service, library
):
    file = io.BytesIO(stub_bib.as_marc())
    data_dict = stub_template.__dict__
    data_dict.update({"library": library})
    response = client.post(
        "/vendor_file",
        files={"marc_file": file},
        data=data_dict,
    )
    assert response.text == ""
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/vendor_file"
    assert "Order File" in response.text
    assert "Enter Template Data" in response.text


@pytest.mark.parametrize("library", ["foo"])
def test_process_vendor_file_post_invalid_config(stub_bib, stub_template, library):
    file = io.BytesIO(stub_bib.as_marc())
    with pytest.raises(ValueError) as exc:
        client.post(
            "/vendor_file",
            files={"marc_file": file},
            data=stub_template.__dict__,
        )
    assert "Invalid library. Must be 'bpl' or 'nypl'" in str(exc.value)
