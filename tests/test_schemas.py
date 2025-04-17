import pytest

from overload_web.domain import model
from overload_web.presentation.api import schemas


def test_OrderModel(order_data):
    order = schemas.OrderModel(**order_data)
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
def test_BibModel(order_data, library):
    stub_domain_bib = model.DomainBib(
        library=library, orders=[model.Order(**order_data)]
    )
    bib = schemas.BibModel(**stub_domain_bib.__dict__)
    assert bib.model_dump() == {
        "bib_id": None,
        "isbn": None,
        "upc": None,
        "oclc_number": None,
        "orders": [order_data],
        "library": library,
    }


def test_TemplateModel(template_data):
    template = schemas.TemplateModel(**template_data)
    assert template.model_dump() == template_data
