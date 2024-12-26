from datetime import datetime
import pytest
from overload_web.domain.model import (
    OrderBib,
    Order,
    OrderTemplate,
    apply_template,
)


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_Order(library):
    order = Order(
        isbn="9781234567890",
        library=library,
        create_date=datetime(2024, 1, 1),
        locations=["(4)fwa0f", "(2)bca0f", "gka0f"],
        shelves=["0f", "0f", "0f"],
        price="$5.00",
        fund="25240adbk",
        copies="7",
        lang="eng",
        country="xxu",
        vendor_code="0049",
        format="a",
        selector="b",
        audience=["a", "a", "a"],
        source="d",
        order_type="p",
        status="o",
        internal_note=None,
        var_field_isbn=None,
        vendor_notes=None,
        vendor_title_no=None,
        blanket_po=None,
    )
    assert order.isbn == "9781234567890"
    assert order.oclc_number is None
    assert order.upc is None
    assert order.bib_id is None


def test_OrderTemplate():
    template = OrderTemplate(
        datetime(2024, 1, 1),
        ["(4)fwa0f", "(2)bca0f", "gka0f"],
        ["0f", "0f"],
        "$5.00",
        "25240adbk",
        "7",
        "eng",
        "xxu",
        "0049",
        "a",
        "b",
        ["a", "a", "a"],
        "d",
        "p",
        "o",
        None,
        None,
        None,
        None,
        None,
    )
    assert template.create_date == datetime(2024, 1, 1)
    assert template.locations == ["(4)fwa0f", "(2)bca0f", "gka0f"]
    assert template.shelves == ["0f", "0f"]
    assert template.price == "$5.00"
    assert template.fund == "25240adbk"
    assert template.copies == "7"
    assert template.lang == "eng"
    assert template.country == "xxu"
    assert template.vendor_code == "0049"
    assert template.format == "a"
    assert template.selector == "b"
    assert template.audience == ["a", "a", "a"]
    assert template.source == "d"
    assert template.order_type == "p"
    assert template.status == "o"
    assert template.internal_note is None
    assert template.isbn is None
    assert template.vendor_notes is None
    assert template.vendor_title_no is None
    assert template.blanket_po is None
    assert template.primary_matchpoint is None
    assert template.secondary_matchpoint is None
    assert template.tertiary_matchpoint is None
    assert template.matchpoints == []


def test_OrderBib(stub_order):
    bib = OrderBib(order=stub_order)
    assert stub_order.bib_id is None
    assert bib.bib_id is None


def test_OrderBib_bib_id(stub_order):
    order = stub_order
    order.bib_id = "b123456789"
    bib = OrderBib(order=order)
    assert bib.bib_id == "b123456789"


def test_model_apply_template(stub_template, stub_order):
    bib = OrderBib(order=stub_order)
    assert bib.fund == "25240adbk"
    updated_bib = apply_template(bib, stub_template)
    assert updated_bib.fund == "10001adbk"
