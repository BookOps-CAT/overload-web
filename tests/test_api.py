from dataclasses import asdict
from fastapi.testclient import TestClient
import pytest
from overload_web.main import app
from overload_web import schemas


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"application": "Overload Web"}


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_attach_endpoint(stub_order):
    order_schema = schemas.OrderModel(**asdict(stub_order)).model_dump()
    data = {
        "order": order_schema,
        "bib_ids": ["123456789", "987654321"],
    }
    response = client.post("/attach", json=data)
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/attach"
    assert response.json()["bib"]["all_bib_ids"] == ["123456789", "987654321"]


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_vendor_file_endpoint(stub_order, stub_template, stub_sierra_service):
    template_schema = schemas.OrderTemplateModel(**asdict(stub_template)).model_dump()
    order_schema = schemas.OrderModel(**asdict(stub_order)).model_dump()
    data = {"order": order_schema, "template": template_schema}
    response = client.post("/vendor_file", json=data)
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/vendor_file"
    assert response.json()["bib"]["fund"] == "10001adbk" == template_schema["fund"]
    assert response.json()["bib"]["fund"] != order_schema["fund"]


@pytest.mark.parametrize("library", ["foo"])
def test_process_vendor_file_endpoint_invalid_config(stub_order, stub_template):
    template_schema = schemas.OrderTemplateModel(**asdict(stub_template)).model_dump()
    order_schema = schemas.OrderModel(**asdict(stub_order)).model_dump()
    data = {"order": order_schema, "template": template_schema}
    with pytest.raises(ValueError) as exc:
        client.post("/vendor_file", json=data)
    assert "Invalid library. Must be 'bpl' or 'nypl'" in str(exc.value)
