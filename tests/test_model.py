from datetime import datetime
import pytest
from src.overload_web.domain.model import (
    OrderBib,
    Order,
    FixedOrderData,
    VariableOrderData,
    attach,
    match,
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


@pytest.mark.parametrize(
    "num, expectation", [("b123456789", "b123456789"), ("b111111111", None)]
)
def test_match_bib_id(stub_Order, stub_OrderBib, num, expectation):
    stub_Order.bib_id = num
    matched_id = match(stub_Order, stub_OrderBib, ["bib_id"])
    assert matched_id == expectation


@pytest.mark.parametrize(
    "num, expectation", [("ocm00000123", "b123456789"), ("(OCoLC)1234567890", None)]
)
def test_match_oclc_number(stub_Order, stub_OrderBib, num, expectation):
    stub_Order.oclc_number = num
    matched_id = match(stub_Order, stub_OrderBib, ["oclc_number"])
    assert matched_id == expectation


@pytest.mark.parametrize(
    "num, expectation", [("9781234567890", "b123456789"), ("1111111111", None)]
)
def test_match_isbn(stub_Order, stub_OrderBib, num, expectation):
    stub_Order.isbn = num
    matched_id = match(stub_Order, stub_OrderBib, ["isbn"])
    assert matched_id == expectation


@pytest.mark.parametrize(
    "num, expectation", [("123456", "b123456789"), ("654321", None)]
)
def test_match_upc(stub_Order, stub_OrderBib, num, expectation):
    stub_Order.upc = num
    matched_id = match(stub_Order, stub_OrderBib, ["upc"])
    assert matched_id == expectation
