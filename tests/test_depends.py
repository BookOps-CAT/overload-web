import datetime
import io

import pytest
from fastapi import UploadFile

from overload_web.adapters import depends


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_order_mapper(stub_bib):
    orders = depends.order_mapper(stub_bib)
    assert len(orders) == 1
    assert orders[0].audience == "a"
    assert stub_bib.orders[0].created == orders[0].create_date
    assert orders[0].create_date == datetime.date(2025, 1, 1)
    assert orders[0].internal_note == "foo"


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_order_mapper_end_of_record(stub_bib):
    stub_bib.remove_fields("961")
    orders = depends.order_mapper(stub_bib)
    assert len(orders) == 1
    assert orders[0].audience == "a"
    assert stub_bib.orders[0].created == orders[0].create_date
    assert orders[0].create_date == datetime.date(2025, 1, 1)
    assert orders[0].internal_note is None


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_order_mapper_no_960(stub_bib):
    stub_bib.remove_fields("960", "961")
    orders = depends.order_mapper(stub_bib)
    assert orders == []


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_read_marc_file(stub_bib, library):
    bib_file = UploadFile(file=io.BytesIO(stub_bib.as_marc()), filename="test.mrc")
    bib_list = depends.read_marc_file(bib_file, library)
    assert len(bib_list) == 1


@pytest.mark.parametrize(
    "library, destination", [("nypl", "branches"), ("nypl", "research"), ("bpl", None)]
)
def test_process_input(stub_pvf_form_data, stub_bib, library, destination):
    bib_file = UploadFile(file=io.BytesIO(stub_bib.as_marc()), filename="test.mrc")
    data, records = depends.process_input(file=bib_file, form_data=stub_pvf_form_data)
    assert hasattr(data, "library")
    assert hasattr(data, "destination")
    assert hasattr(data, "template_data")
    assert len(records) == 1
    assert hasattr(records[0], "library")
    assert records[0].library == library
