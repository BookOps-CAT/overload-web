import datetime

import pytest

from overload_web.api import schemas
from overload_web.domain import model


def test_OrderModel(stub_order):
    order = schemas.OrderModel(**stub_order.__dict__)
    assert order.model_dump() == {
        "create_date": "2024-01-01",
        "locations": ["(4)fwa0f", "(2)bca0f", "gka0f"],
        "price": "$5.00",
        "fund": "25240adbk",
        "copies": "7",
        "lang": "eng",
        "country": "xxu",
        "vendor_code": "0049",
        "format": "a",
        "selector": "b",
        "selector_note": None,
        "audience": "a",
        "source": "d",
        "order_type": "p",
        "status": "o",
        "internal_note": None,
        "var_field_isbn": None,
        "vendor_notes": None,
        "vendor_title_no": None,
        "blanket_po": None,
    }


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_BibModel(stub_order, library):
    stub_domain_bib = model.DomainBib(library=library, orders=[stub_order])
    bib = schemas.BibModel(**stub_domain_bib.__dict__)
    assert bib.model_dump() == {
        "bib_id": None,
        "isbn": None,
        "upc": None,
        "oclc_number": None,
        "orders": [stub_order.__dict__],
        "library": library,
    }


def test_TemplateModel(stub_template):
    template = schemas.TemplateModel(**stub_template.__dict__)
    assert template.model_dump() == stub_template.__dict__


def test_PersistentTemplateModel(stub_template):
    template_data = stub_template.__dict__
    template_data.update(
        {
            "id": 1,
            "name": "Foo Template",
            "agent": "user1",
            "create_date": datetime.date(2024, 1, 1),
        }
    )
    template = schemas.PersistentTemplateModel(**template_data)
    assert template.model_dump() == template_data
