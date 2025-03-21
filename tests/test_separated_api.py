import io

import pytest
from fastapi.testclient import TestClient

from overload_web.api.overload_api import api_router

client = TestClient(api_router)


def test_root_get():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"app": "Overload Web"}


@pytest.mark.parametrize(
    "library, destination", [("nypl", "branches"), ("nypl", "research"), ("bpl", None)]
)
def test_process_vendor_file_post(
    stub_pvf_form_data, stub_bib, stub_sierra_service, library, destination
):
    response = client.post(
        "/vendor_file",
        files={"file": ("marc_file.mrc", io.BytesIO(stub_bib.as_marc()), "text/plain")},
        data=stub_pvf_form_data,
    )
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/vendor_file"
    assert len(response.json()["template"].keys()) == len(stub_pvf_form_data.keys()) - 2
    assert isinstance(response.json()["processed_bibs"], list)


@pytest.mark.parametrize(
    "library, destination", [("foo", "branches"), ("bar", "research")]
)
def test_process_vendor_file_post_invalid_config(
    stub_bib, stub_pvf_form_data, library, destination
):
    with pytest.raises(ValueError) as exc:
        client.post(
            "/vendor_file",
            files={
                "file": ("marc_file.mrc", io.BytesIO(stub_bib.as_marc()), "text/plain")
            },
            data=stub_pvf_form_data,
        )
    assert "Invalid library. Must be 'bpl' or 'nypl'" in str(exc.value)
