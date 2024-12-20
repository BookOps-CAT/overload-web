import pytest
from overload_web.domain import model
from overload_web.sierra_adapters import AbstractSierraSession
from overload_web import services


class FakeSierraSession(AbstractSierraSession):
    def __init__(self):
        pass

    def _get_credentials(self):
        return super()._get_credentials()

    def _get_target(self):
        return super()._get_target()

    def _search_by_id(self, key: str, value: str | int) -> list:
        if key and value:
            return ["123456789"]
        else:
            return []


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_apply_template(
    stub_order_fixed_field, stub_order_variable_field, library, stub_template
):
    order = model.Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    bib = model.OrderBib(order=order)
    assert bib.fund == "25240adbk"
    new_bib = services.apply_template(bib, stub_template)
    assert new_bib.fund == "10001adbk"


@pytest.mark.parametrize(
    "library, matched_bib",
    [("bpl", "123456789"), ("nypl", "123456789"), ("bpl", None), ("nypl", None)],
)
def test_attach(
    stub_order_fixed_field, stub_order_variable_field, library, matched_bib
):
    order = model.Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    bib = services.attach(order, matched_bib)
    assert isinstance(bib, model.OrderBib)
    assert bib.bib_id == matched_bib
    assert order.bib_id is None


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_process_file(
    stub_template, library, stub_order_fixed_field, stub_order_variable_field
):
    session = FakeSierraSession()
    order = model.Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    order.isbn = "9781234567890"
    processed_bib = services.process_file(session, order, stub_template)
    assert order.fixed_field.fund == "25240adbk"
    assert order.bib_id is None
    assert processed_bib.fund == stub_template.fund == "10001adbk"
    assert processed_bib.bib_id == "123456789"


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_process_file_no_matchpoints(
    stub_template, library, stub_order_fixed_field, stub_order_variable_field
):
    session = FakeSierraSession()
    order = model.Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    stub_template.primary_matchpoint = None
    processed_bib = services.process_file(session, order, stub_template)
    assert order.bib_id is None
    assert processed_bib.fund == stub_template.fund == "10001adbk"
    assert processed_bib.fund != order.fixed_field.fund
    assert processed_bib.bib_id is None


@pytest.mark.parametrize("library", ["bpl", "nypl"])
def test_process_file_no_match(
    stub_template, library, stub_order_fixed_field, stub_order_variable_field
):
    session = FakeSierraSession()
    order = model.Order(
        fixed_field=stub_order_fixed_field,
        variable_field=stub_order_variable_field,
        library=library,
    )
    order.isbn = None
    processed_bib = services.process_file(session, order, stub_template)
    assert order.bib_id is None
    assert processed_bib.fund == stub_template.fund == "10001adbk"
    assert processed_bib.fund != order.fixed_field.fund
    assert processed_bib.bib_id is None
