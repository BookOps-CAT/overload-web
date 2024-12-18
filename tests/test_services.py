from typing import List
import pytest
from overload_web.domain import model
from overload_web.sierra_adapters import AbstractSierraSession
from overload_web import services


class FakeSierraSession(AbstractSierraSession):
    def __init__(self):
        pass

    def _match_order(self, order: model.Order, matchpoints: List[str]):
        return [f"{order.bib_id}"]


@pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
def test_attach_bpl(matchpoint, stub_bpl_order):
    adapter = FakeSierraSession()
    matched_bib = services.match(stub_bpl_order, adapter, matchpoints=[matchpoint])
    bib = services.attach(stub_bpl_order, matched_bib[0])
    assert isinstance(bib, model.OrderBib)
    assert bib.bib_id == "123456789"


@pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
def test_attach_nypl(matchpoint, stub_nypl_order):
    adapter = FakeSierraSession()
    matched_bib = services.match(stub_nypl_order, adapter, matchpoints=[matchpoint])
    bib = services.attach(stub_nypl_order, matched_bib[0])
    assert isinstance(bib, model.OrderBib)
    assert bib.bib_id == "123456789"


@pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
def test_match_bpl(matchpoint, stub_bpl_order):
    adapter = FakeSierraSession()
    matched_bib = services.match(stub_bpl_order, adapter, matchpoints=[matchpoint])
    assert matched_bib == ["123456789"]


@pytest.mark.parametrize("matchpoint", ["isbn", "upc", "oclc_number", "bib_id"])
def test_match_nypl(matchpoint, stub_nypl_order):
    adapter = FakeSierraSession()
    matched_bib = services.match(stub_nypl_order, adapter, matchpoints=[matchpoint])
    assert matched_bib == ["123456789"]


def test_apply_template_bpl(stub_nypl_order, stub_template):
    bib = model.OrderBib(order=stub_nypl_order)
    assert bib.fund == "25240adbk"
    new_bib = services.apply_template(bib, stub_template)
    assert new_bib.fund == "10001adbk"
