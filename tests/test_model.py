from datetime import datetime
import pytest
from overload_web.domain.model import (
    OrderBib,
    Order,
    OrderTemplate,
    apply_template,
)


def test_Order():
    order = Order(
        create_date=datetime(2024, 1, 1),
        locations=["(4)fwa0f", "(2)bca0f", "gka0f"],
        price="$5.00",
        fund="25240adbk",
        copies="7",
        lang="eng",
        country="xxu",
        vendor_code="0049",
        format="a",
        selector="b",
        selector_note=None,
        audience="a",
        source="d",
        order_type="p",
        status="o",
        internal_note=None,
        var_field_isbn=None,
        vendor_notes=None,
        vendor_title_no=None,
        blanket_po=None,
    )
    assert order.price == "$5.00"
    assert order.format == "a"
    assert order.blanket_po is None


def test_OrderTemplate():
    template = OrderTemplate(
        audience="a",
        blanket_po=None,
        copies="7",
        country="xxu",
        create_date=datetime(2024, 1, 1),
        format="a",
        fund="25240adbk",
        internal_note=None,
        lang="eng",
        order_type="p",
        price="$5.00",
        selector="b",
        selector_note=None,
        source="d",
        status="o",
        var_field_isbn=None,
        vendor_code="0049",
        vendor_notes=None,
        vendor_title_no=None,
        primary_matchpoint=None,
        secondary_matchpoint=None,
        tertiary_matchpoint=None,
    )
    assert template.create_date == datetime(2024, 1, 1)
    assert template.price == "$5.00"
    assert template.fund == "25240adbk"
    assert template.copies == "7"
    assert template.lang == "eng"
    assert template.country == "xxu"
    assert template.vendor_code == "0049"
    assert template.format == "a"
    assert template.selector == "b"
    assert template.selector_note is None
    assert template.audience == "a"
    assert template.source == "d"
    assert template.order_type == "p"
    assert template.status == "o"
    assert template.internal_note is None
    assert template.var_field_isbn is None
    assert template.vendor_notes is None
    assert template.vendor_title_no is None
    assert template.blanket_po is None
    assert template.primary_matchpoint is None
    assert template.secondary_matchpoint is None
    assert template.tertiary_matchpoint is None
    assert template.matchpoints == []


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_OrderBib(library, stub_order):
    bib = OrderBib(library=library, orders=[stub_order])
    assert bib.bib_id is None


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_OrderBib_bib_id(library, stub_order):
    order = stub_order
    bib = OrderBib(library=library, orders=[order], bib_id="b123456789")
    assert bib.bib_id == "b123456789"


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_model_apply_template(library, stub_template, stub_order):
    bib = OrderBib(library=library, orders=[stub_order])
    assert bib.orders[0].fund == "25240adbk"
    updated_bib = apply_template(bib, stub_template)
    assert updated_bib.orders[0].fund == "10001adbk"
