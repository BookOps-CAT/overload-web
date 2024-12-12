from datetime import datetime
from src.overload_web.domain.model import ModelBib, OrderFixedField, OrderVariableField


def test_ModelBib(stub_order_fixed_field, stub_order_variable_field):
    bib = ModelBib(
        bib_format="b",
        control_number="ocm00001234",
        library="nypl",
        order_fixed_field=stub_order_fixed_field,
        order_variable_field=stub_order_variable_field,
    )
    assert bib.bib_id is None


def test_ModelBib_eq(stub_ModelBib, stub_order_fixed_field, stub_order_variable_field):
    bib = ModelBib(
        "b",
        "ocm00001234",
        "nypl",
        stub_order_fixed_field,
        stub_order_variable_field,
    )
    other_bib = ModelBib(
        "b",
        "ocm00000001",
        "nypl",
        stub_order_fixed_field,
        stub_order_variable_field,
    )
    assert bib != stub_ModelBib
    assert other_bib == stub_ModelBib
    other_bib.library = "bpl"
    assert other_bib != stub_ModelBib


def test_ModelBib_eq_false(stub_ModelBib):
    other_bib = "Bib"
    assert stub_ModelBib != other_bib


def test_ModelBib_merge_bib_id(
    stub_ModelBib, stub_order_fixed_field, stub_order_variable_field
):
    other_bib = ModelBib(
        "b",
        "ocm00000001",
        "nypl",
        stub_order_fixed_field,
        stub_order_variable_field,
        "b123456789",
    )
    assert stub_ModelBib.bib_id is None
    stub_ModelBib.merge_bib_id(other_bib)
    assert stub_ModelBib.bib_id == "b123456789"


def test_OrderFixedField():
    order_data = OrderFixedField(
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


def test_OrderVariableField():
    order_data = OrderVariableField(
        None, ["9781101906118", "1101906111"], "HOLDS", None, None
    )
    assert order_data.isbn == ["9781101906118", "1101906111"]
