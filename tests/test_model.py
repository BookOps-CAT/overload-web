from datetime import datetime
import pytest
from overload_web.domain.model import (
    OrderBib,
    Order,
    OrderTemplate,
    FixedOrderData,
    VariableOrderData,
    apply_template,
    attach,
)


def test_Order(stub_order_fixed_field, stub_order_variable_field):
    order = Order(
        fixed_field=stub_order_fixed_field,
        library="nypl",
        variable_field=stub_order_variable_field,
        isbn="9781234567890",
    )
    assert order.isbn == "9781234567890"
    assert order.oclc_number is None
    assert order.upc is None
    assert order.bib_id is None
    assert order.fixed_field is not None
    assert order.variable_field is not None
    assert isinstance(order.fixed_field, FixedOrderData)
    assert isinstance(order.variable_field, VariableOrderData)


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


def test_FixedOrderData():
    order_data = FixedOrderData(
        datetime(2024, 12, 12),
        ["fwa0f"],
        ["0f"],
        "$5.00",
        "25240adbk",
        "1",
        "eng",
        "xxu",
        "0049",
        "a",
        "b",
        ["a"],
        "d",
        "p",
        "o",
    )
    assert order_data.price == "$5.00"
    assert order_data.fund == "25240adbk"


def test_VariableOrderData():
    order_data = VariableOrderData(
        None, ["9781101906118", "1101906111"], "HOLDS", None, None
    )
    assert order_data.isbn == ["9781101906118", "1101906111"]


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_OrderBib(library, stub_order_fixed_field, stub_order_variable_field):
    order = Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    bib = OrderBib(order=order)
    assert order.bib_id is None
    assert bib.bib_id is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_OrderBib_bib_id(library, stub_order_fixed_field, stub_order_variable_field):
    order = Order(
        stub_order_fixed_field, library, stub_order_variable_field, "b123456789"
    )
    bib = OrderBib(order=order)
    assert bib.bib_id == "b123456789"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_model_attach(library, stub_order_fixed_field, stub_order_variable_field):
    order = Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    bib = OrderBib(order=order)
    assert bib.bib_id is None
    new_bib = attach(order, "b111111111")
    assert new_bib.bib_id == "b111111111"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_model_apply_template(
    library, stub_template, stub_order_fixed_field, stub_order_variable_field
):
    order = Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    bib = OrderBib(order=order)
    assert bib.fund == "25240adbk"
    updated_bib = apply_template(bib, stub_template)
    assert updated_bib.fund == "10001adbk"
