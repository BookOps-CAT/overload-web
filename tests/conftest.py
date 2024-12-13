from datetime import datetime
import pytest
from src.overload_web.domain.model import (
    Order,
    OrderBib,
    FixedOrderData,
    VariableOrderData,
)


@pytest.fixture
def stub_Order(stub_order_fixed_field, stub_order_variable_field):
    return Order(
        fixed_field=stub_order_fixed_field,
        library="nypl",
        variable_field=stub_order_variable_field,
    )


@pytest.fixture
def stub_OrderBib(stub_Order):
    order = stub_Order
    order.isbn = "9781234567890"
    order.oclc_number = "ocm00000123"
    order.upc = "123456"
    return OrderBib(order, bib_id="b123456789")


@pytest.fixture
def stub_order_fixed_field():
    return FixedOrderData(
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
    )


@pytest.fixture
def stub_order_variable_field():
    return VariableOrderData(None, "9780123456789", "NEW", None, None)
