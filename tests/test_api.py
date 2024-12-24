from dataclasses import asdict
from fastapi.testclient import TestClient
import pytest
from overload_web.main import app
from overload_web import schemas

client = TestClient(app)


@pytest.fixture
def stub_template_base_model(stub_template):
    return schemas.OrderTemplateModel(**asdict(stub_template))


@pytest.fixture
def stub_order_base_model(stub_order):
    return schemas.OrderModel(**asdict(stub_order))


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"application": "Overload Web"}


def test_attach_endpoint(stub_order_base_model):
    data = {
        "order": stub_order_base_model.model_dump(),
        "bib_ids": ["123456789", "987654321"],
    }
    response = client.post("/attach", json=data)
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/attach"
    assert response.json()["bib"]["all_bib_ids"] == ["123456789", "987654321"]


def test_process_vendor_file_endpoint(stub_order_base_model, stub_template_base_model):
    data = {
        "order": stub_order_base_model.model_dump(),
        "template": stub_template_base_model.model_dump(),
    }
    response = client.post("/vendor_file", json=data)
    assert response.status_code == 200
    assert response.url == f"{client.base_url}/vendor_file"
    assert (
        response.json()["bib"]["fund"]
        == "10001adbk"
        == stub_template_base_model.model_dump()["fund"]
    )
    assert response.json()["bib"]["fund"] != stub_order_base_model.model_dump()["fund"]
