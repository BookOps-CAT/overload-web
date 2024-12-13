from datetime import datetime
from src.overload_web.domain.model import (
    OrderBib,
    Order,
    FixedOrderData,
    VariableOrderData,
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
    assert order.control_number is None
    assert order.bib_id is None
    assert order.fixed_field is not None
    assert order.variable_field is not None
    assert isinstance(order.fixed_field, FixedOrderData)
    assert isinstance(order.variable_field, VariableOrderData)


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


def test_OrderBib(stub_Order):
    bib = OrderBib(order=stub_Order)
    other_bib = OrderBib(order=stub_Order, bib_id="b123456789")
    assert bib.bib_id is None
    assert other_bib.bib_id == "b123456789"


def test_OrderBib_bib_id(stub_order_fixed_field, stub_order_variable_field):
    order = Order(
        stub_order_fixed_field, "nypl", stub_order_variable_field, "b123456789"
    )
    bib = OrderBib(order=order)
    assert bib.bib_id == "b123456789"


def test_OrderBib_attach(stub_Order):
    bib = OrderBib(stub_Order)
    assert bib.bib_id is None
    bib.attach("b111111111")
    assert bib.bib_id == "b111111111"


def test_attach(stub_Order):
    order = attach(stub_Order, "b111111111")
    assert isinstance(order, OrderBib)
    assert order.bib_id == "b111111111"
