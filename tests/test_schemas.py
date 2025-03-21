import datetime
import io

import pytest
from fastapi import UploadFile

from overload_web.adapters import schemas
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


def test_OrderTemplateModel(stub_template):
    template = schemas.OrderTemplateModel(**stub_template.__dict__)
    assert template.model_dump() == stub_template.__dict__


def test_OverloadOrder(stub_960, stub_961):
    order = schemas.OverloadOrder(stub_960, stub_961)
    assert order.audience == "a"
    assert order.blanket_po == "baz"
    assert order.copies == 13
    assert order.country == "xxu"
    assert order.created == datetime.date(2025, 1, 1)
    assert order.form == "b"
    assert order.fund == "lease"
    assert order.internal_note == "foo"
    assert order.lang == "eng"
    assert order.locs == ["agj0y"]
    assert order.order_type == "l"
    assert order.price == "{{dollar}}13.20"
    assert order.selector == "j"
    assert order.source == "d"
    assert order.status == "o"
    assert order.var_field_isbn == "bar"
    assert order.vendor_code == "btlea"
    assert order.venNotes == "baz"
    assert order.vendor_title_no == "foo"


def test_OverloadOrder_no_var_fields(stub_960):
    order = schemas.OverloadOrder(stub_960)
    assert order.audience == "a"
    assert order.blanket_po is None
    assert order.copies == 13
    assert order.country == "xxu"
    assert order.created == datetime.date(2025, 1, 1)
    assert order.form == "b"
    assert order.fund == "lease"
    assert order.internal_note is None
    assert order.lang == "eng"
    assert order.locs == ["agj0y"]
    assert order.order_type == "l"
    assert order.price == "{{dollar}}13.20"
    assert order.selector == "j"
    assert order.selector_note is None
    assert order.source == "d"
    assert order.status == "o"
    assert order.var_field_isbn is None
    assert order.vendor_code == "btlea"
    assert order.venNotes is None
    assert order.vendor_title_no is None


@pytest.mark.parametrize(
    "library, destination", [("nypl", "branches"), ("nypl", "research"), ("bpl", None)]
)
def test_ProcessVendorFileForm(stub_template, library, destination):
    form_dict = stub_template.__dict__
    form_dict["library"] = library
    form_dict["destination"] = destination
    form_data = schemas.ProcessVendorFileForm(**form_dict)
    model_data = form_data.model_dump()
    assert model_data["library"] == library
    assert model_data["destination"] == destination
    assert model_data.keys() == form_dict.keys()


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
