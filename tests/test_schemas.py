import datetime
import io

import pytest
from fastapi import UploadFile

from overload_web.api import schemas
from overload_web.domain import model


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_OrderBibModel(stub_order, library):
    stub_orderbib = model.OrderBib(library=library, orders=[stub_order])
    order_bib = schemas.OrderBibModel(**stub_orderbib.__dict__)
    assert order_bib.model_dump() == {
        "bib_id": None,
        "isbn": None,
        "upc": None,
        "oclc_number": None,
        "orders": [stub_order.__dict__],
        "library": library,
    }


def test_TemplateModel(stub_template):
    template = schemas.TemplateModel(**stub_template.__dict__)
    assert template.model_dump() == stub_template.__dict__


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_order_mapper(stub_bib):
    orders = schemas.order_mapper(stub_bib)
    assert len(orders) == 1
    assert orders[0].audience == "a"
    assert stub_bib.orders[0].created == orders[0].create_date
    assert orders[0].create_date == datetime.date(2025, 1, 1)
    assert orders[0].internal_note == "foo"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_order_mapper_end_of_record(stub_bib):
    stub_bib.remove_fields("961")
    orders = schemas.order_mapper(stub_bib)
    assert len(orders) == 1
    assert orders[0].audience == "a"
    assert stub_bib.orders[0].created == orders[0].create_date
    assert orders[0].create_date == datetime.date(2025, 1, 1)
    assert orders[0].internal_note is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_order_mapper_no_960(stub_bib):
    stub_bib.remove_fields("960", "961")
    orders = schemas.order_mapper(stub_bib)
    assert orders == []


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_read_marc_file(stub_bib, library):
    bib_file = UploadFile(file=io.BytesIO(stub_bib.as_marc()), filename="test.mrc")
    bib_list = schemas.read_marc_file(bib_file, library)
    assert len(bib_list) == 1
