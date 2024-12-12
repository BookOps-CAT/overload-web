from datetime import datetime
import pytest
from src.overload_web.domain.model import ModelBib, OrderFixedField, OrderVariableField


@pytest.fixture
def stub_ModelBib(stub_order_fixed_field, stub_order_variable_field):
    return ModelBib(
        bib_format="b",
        control_number="ocm00000001",
        library="nypl",
        order_fixed_field=stub_order_fixed_field,
        order_variable_field=stub_order_variable_field,
    )


@pytest.fixture
def stub_order_fixed_field():
    return OrderFixedField(
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
    return OrderVariableField(None, "9780123456789", "NEW", None, None)
