import datetime

import pytest

from overload_web.adapters import schemas
from overload_web.domain import model


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_OrderBibModel(stub_order, library):
    stub_orderbib = model.OrderBib(library=library, orders=[stub_order])
    order_bib = schemas.OrderBibModel(**stub_orderbib.__dict__)
    assert order_bib.model_dump() == {
        "bib_id": None,
        "isbn": None,
        "upc": None,
        "oclc_number": None,
        "orders": [stub_order.__dict__],
        "library": library,
    }


def test_OrderTemplateModel(stub_template):
    template = schemas.OrderTemplateModel(**stub_template.__dict__)
    assert template.model_dump() == stub_template.__dict__


def test_OverloadOrder(stub_960, stub_961):
    order = schemas.OverloadOrder(stub_960, stub_961)
    assert order.audience == "a"
    assert order.blanket_po == "baz"
    assert order.copies == 13
    assert order.country == "xxu"
    assert order.created == datetime.date(2025, 1, 1)
    assert order.form == "b"
    assert order.fund == "lease"
    assert order.internal_note == "foo"
    assert order.lang == "eng"
    assert order.locs == ["agj0y"]
    assert order.order_type == "l"
    assert order.price == "{{dollar}}13.20"
    assert order.selector == "j"
    assert order.source == "d"
    assert order.status == "o"
    assert order.var_field_isbn == "bar"
    assert order.vendor_code == "btlea"
    assert order.venNotes == "baz"
    assert order.vendor_title_no == "foo"


def test_OverloadOrder_no_var_fields(stub_960):
    order = schemas.OverloadOrder(stub_960)
    assert order.audience == "a"
    assert order.blanket_po is None
    assert order.copies == 13
    assert order.country == "xxu"
    assert order.created == datetime.date(2025, 1, 1)
    assert order.form == "b"
    assert order.fund == "lease"
    assert order.internal_note is None
    assert order.lang == "eng"
    assert order.locs == ["agj0y"]
    assert order.order_type == "l"
    assert order.price == "{{dollar}}13.20"
    assert order.selector == "j"
    assert order.selector_note is None
    assert order.source == "d"
    assert order.status == "o"
    assert order.var_field_isbn is None
    assert order.vendor_code == "btlea"
    assert order.venNotes is None
    assert order.vendor_title_no is None


@pytest.mark.parametrize(
    "library, destination", [("nypl", "branches"), ("nypl", "research"), ("bpl", None)]
)
def test_ProcessVendorFileForm(stub_template, library, destination):
    form_data = schemas.ProcessVendorFileForm(
        library=library, destination=destination, template_data=stub_template.__dict__
    )
    assert form_data.model_dump() == {
        "library": library,
        "destination": destination,
        "template_data": stub_template.__dict__,
    }
