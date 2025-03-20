import pytest

from overload_web.domain import model
from overload_web.services import handlers


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_apply_template(stub_order, stub_template):
    bib = model.OrderBib(order=stub_order)
    assert bib.fund == "25240adbk"
    new_bib = handlers.apply_template(bib, stub_template)
    assert new_bib.fund == "10001adbk"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
@pytest.mark.parametrize("all_bibs, bib_id", [(["123456789"], "123456789"), ([], None)])
def test_attach(stub_order, all_bibs, bib_id):
    bib = handlers.attach(stub_order, all_bibs)
    assert isinstance(bib, model.OrderBib)
    assert bib.all_bib_ids == all_bibs
    assert bib.bib_id == bib_id
    assert stub_order.bib_id is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_file(stub_template, stub_order, stub_sierra_service):
    stub_order.isbn = "9781234567890"
    processed_bib = handlers.process_file(
        stub_sierra_service, stub_order, stub_template
    )
    assert stub_order.fund == "25240adbk"
    assert stub_order.bib_id is None
    assert processed_bib.fund == stub_template.fund == "10001adbk"
    assert processed_bib.bib_id == "123456789"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_file_no_matchpoints(stub_template, stub_order, stub_sierra_service):
    stub_template.primary_matchpoint = None
    processed_bib = handlers.process_file(
        stub_sierra_service, stub_order, stub_template
    )
    assert stub_order.bib_id is None
    assert processed_bib.fund == stub_template.fund == "10001adbk"
    assert processed_bib.fund != stub_order.fund
    assert processed_bib.bib_id is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_file_no_match(stub_template, stub_order, stub_sierra_service):
    stub_order.isbn = None
    processed_bib = handlers.process_file(
        stub_sierra_service, stub_order, stub_template
    )
    assert stub_order.bib_id is None
    assert processed_bib.fund == stub_template.fund == "10001adbk"
    assert processed_bib.fund != stub_order.fund
    assert processed_bib.bib_id is None
