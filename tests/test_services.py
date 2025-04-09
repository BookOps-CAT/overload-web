import pytest

from overload_web.services import handlers


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_apply_template(stub_domain_bib, stub_template):
    original_fund = stub_domain_bib.orders[0].fund
    new_bib = handlers.apply_template(bib=stub_domain_bib, template=stub_template)
    assert new_bib.orders[0].fund == "10001adbk"
    assert original_fund == "25240adbk"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_file(stub_template, stub_domain_bib, stub_sierra_service):
    stub_domain_bib.isbn = "9781234567890"
    original_fund = stub_domain_bib.orders[0].fund
    processed_bib = handlers.process_file(
        sierra_service=stub_sierra_service,
        bib=stub_domain_bib,
        template=stub_template,
    )

    assert processed_bib.orders[0].fund == stub_template.fund == "10001adbk"
    assert original_fund != processed_bib.orders[0].fund
    assert original_fund != stub_template.fund
    assert processed_bib.bib_id == "123456789"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_file_no_matchpoints(
    stub_template, stub_domain_bib, stub_sierra_service
):
    stub_domain_bib.orders[0].primary_matchpoint = None
    original_fund = stub_domain_bib.orders[0].fund
    processed_bib = handlers.process_file(
        sierra_service=stub_sierra_service,
        bib=stub_domain_bib,
        template=stub_template,
    )
    assert processed_bib.orders[0].fund == stub_template.fund == "10001adbk"
    assert original_fund != processed_bib.orders[0].fund
    assert original_fund != stub_template.fund
    assert processed_bib.bib_id is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_process_file_no_match(stub_template, stub_domain_bib, stub_sierra_service):
    stub_domain_bib.orders[0].isbn = None
    original_fund = stub_domain_bib.orders[0].fund
    processed_bib = handlers.process_file(
        sierra_service=stub_sierra_service,
        bib=stub_domain_bib,
        template=stub_template,
    )

    assert processed_bib.orders[0].fund == stub_template.fund == "10001adbk"
    assert original_fund != processed_bib.orders[0].fund
    assert original_fund != stub_template.fund
    assert processed_bib.bib_id is None
