from __future__ import annotations

import datetime

import pytest

from overload_web.application import marc_adapters, object_factories
from overload_web.domain import model
from overload_web.presentation.api import schemas


@pytest.fixture
def order_data():
    return {
        "audience": "a",
        "blanket_po": "baz",
        "copies": 13,
        "country": "xxu",
        "create_date": datetime.date(2025, 1, 1),
        "format": "b",
        "fund": "lease",
        "internal_note": "foo",
        "lang": "eng",
        "locations": ["agj0y"],
        "order_type": "l",
        "price": "{{dollar}}13.20",
        "selector": "j",
        "selector_note": "bar",
        "source": "d",
        "status": "o",
        "var_field_isbn": "bar",
        "vendor_code": "btlea",
        "vendor_notes": "baz",
        "vendor_title_no": "foo",
    }


@pytest.fixture
def bib_data(library, order_data):
    return {
        "library": library,
        "orders": [model.Order(**order_data)],
        "upc": None,
        "isbn": None,
        "bib_id": None,
        "oclc_number": [],
    }


@pytest.fixture
def stub_order(obj_type, stub_960, stub_961, order_data):
    if obj_type == "domain":
        return model.Order(**order_data)
    elif obj_type == "pydantic":
        return schemas.OrderModel(**order_data)
    elif obj_type == "marc":
        return marc_adapters.OverloadOrder(stub_960, stub_961)
    else:
        return order_data


@pytest.fixture
def stub_bib(obj_type, library, stub_bib, bib_data):
    if obj_type == "domain":
        return model.DomainBib(**bib_data)
    elif obj_type == "pydantic":
        return schemas.BibModel(**bib_data)
    elif obj_type == "marc":
        return marc_adapters.OverloadBib.from_bookops_bib(stub_bib)
    else:
        return bib_data


class TestGenericFactory:
    GENERIC_FACTORY: object_factories.GenericFactory = object_factories.GenericFactory()

    def test_to_dict(self):
        with pytest.raises(NotImplementedError) as exc:
            self.GENERIC_FACTORY.to_dict("foo")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_to_domain(self):
        with pytest.raises(NotImplementedError) as exc:
            self.GENERIC_FACTORY.to_domain("foo")
        assert str(exc.value) == "Subclasses should implement this method."


@pytest.mark.parametrize(
    "obj_type, data_type",
    [
        ("domain", model.Order),
        ("pydantic", schemas.OrderModel),
        ("marc", marc_adapters.OverloadOrder),
    ],
)
class TestOrderFactory:
    ORDER_FACTORY: object_factories.GenericFactory = object_factories.OrderFactory()

    def test_to_domain(self, stub_order, obj_type, data_type, order_data):
        domain_order = model.Order(**order_data)
        order_to_domain = self.ORDER_FACTORY.to_domain(stub_order)
        assert isinstance(stub_order, data_type)
        assert isinstance(order_to_domain, model.Order)
        assert order_to_domain == domain_order

    def test_to_dict(self, stub_order, obj_type, data_type, order_data):
        order_to_dict = self.ORDER_FACTORY.to_dict(stub_order)
        assert isinstance(stub_order, data_type)
        assert isinstance(order_data, dict)
        assert order_data == order_to_dict


@pytest.mark.parametrize(
    "obj_type, data_type",
    [
        ("domain", model.DomainBib),
        ("pydantic", schemas.BibModel),
        ("marc", marc_adapters.OverloadBib),
    ],
)
@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestBibFactory:
    BIB_FACTORY: object_factories.GenericFactory = object_factories.BibFactory()

    def test_to_domain(self, library, stub_bib, data_type, bib_data):
        domain_order_bib = model.DomainBib(**bib_data)
        order_bib_to_domain = self.BIB_FACTORY.to_domain(stub_bib)
        assert isinstance(stub_bib, data_type)
        assert isinstance(order_bib_to_domain, model.DomainBib)
        assert order_bib_to_domain == domain_order_bib

    def test_to_dict(self, stub_bib, obj_type, data_type, bib_data):
        bib_data["orders"] = [i.__dict__ for i in bib_data["orders"]]
        bib_to_dict = self.BIB_FACTORY.to_dict(stub_bib)
        assert isinstance(stub_bib, data_type)
        assert isinstance(bib_data, dict)
        assert bib_data == bib_to_dict
