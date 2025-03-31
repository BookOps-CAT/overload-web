import datetime
import io

import pytest

from overload_web.adapters import marc_adapters


class TestOverloadBib:
    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OverloadBib(self, stub_bib, library):
        bib = marc_adapters.OverloadBib()
        bib.leader = stub_bib.leader
        bib.fields = stub_bib.fields
        bib.library = stub_bib.library
        assert hasattr(bib, "isbn")
        assert hasattr(bib, "sierra_bib_id")
        assert hasattr(bib, "orders")
        assert isinstance(bib, marc_adapters.OverloadBib)
        assert isinstance(bib.orders, list)
        assert isinstance(bib.orders[0], marc_adapters.OverloadOrder)
        assert bib.orders[0].audience == "a"
        assert bib.orders[0].blanket_po == "baz"
        assert bib.orders[0].copies == 13
        assert bib.orders[0].country == "xxu"
        assert bib.orders[0].created == datetime.date(2025, 1, 1)
        assert bib.orders[0].form == "b"
        assert bib.orders[0].fund == "lease"
        assert bib.orders[0].internal_note == "foo"
        assert bib.orders[0].lang == "eng"
        assert bib.orders[0].locs == ["agj0y"]
        assert bib.orders[0].order_type == "l"
        assert bib.orders[0].price == "{{dollar}}13.20"
        assert bib.orders[0].selector == "j"
        assert bib.orders[0].source == "d"
        assert bib.orders[0].status == "o"
        assert bib.orders[0].var_field_isbn == "bar"
        assert bib.orders[0].vendor_code == "btlea"
        assert bib.orders[0].venNotes == "baz"
        assert bib.orders[0].vendor_title_no == "foo"

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OverloadBib_no_following_field(self, stub_bib, library):
        assert stub_bib.orders[0].venNotes == "baz"
        stub_bib.remove_fields("961")
        bib = marc_adapters.OverloadBib.from_bookops_bib(stub_bib)
        assert isinstance(bib.orders, list)
        assert isinstance(bib.orders[0], marc_adapters.OverloadOrder)
        assert bib.orders[0].audience == "a"
        assert bib.orders[0].blanket_po is None
        assert bib.orders[0].copies == 13
        assert bib.orders[0].country == "xxu"
        assert bib.orders[0].created == datetime.date(2025, 1, 1)
        assert bib.orders[0].form == "b"
        assert bib.orders[0].fund == "lease"
        assert bib.orders[0].internal_note is None
        assert bib.orders[0].lang == "eng"
        assert bib.orders[0].locs == ["agj0y"]
        assert bib.orders[0].order_type == "l"
        assert bib.orders[0].price == "{{dollar}}13.20"
        assert bib.orders[0].selector == "j"
        assert bib.orders[0].selector_note is None
        assert bib.orders[0].source == "d"
        assert bib.orders[0].status == "o"
        assert bib.orders[0].var_field_isbn is None
        assert bib.orders[0].vendor_code == "btlea"
        assert bib.orders[0].venNotes is None
        assert bib.orders[0].vendor_title_no is None

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OverloadBib_from_bookops_bib(self, stub_bib, library):
        bib = marc_adapters.OverloadBib.from_bookops_bib(stub_bib)
        assert hasattr(bib, "isbn")
        assert hasattr(bib, "sierra_bib_id")
        assert hasattr(bib, "orders")
        assert isinstance(bib, marc_adapters.OverloadBib)
        assert isinstance(stub_bib, marc_adapters.Bib)
        assert isinstance(bib.orders, list)
        assert isinstance(bib.orders[0], marc_adapters.OverloadOrder)
        assert isinstance(stub_bib.orders[0], marc_adapters.BookopsMarcOrder)
        assert bib.library == stub_bib.library
        assert bib.sierra_bib_id == stub_bib.sierra_bib_id


class TestOverloadOrder:
    def test_OverloadOrder(self, stub_960, stub_961):
        order = marc_adapters.OverloadOrder(stub_960, stub_961)
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

    def test_OverloadOrder_no_var_fields(self, stub_960):
        order = marc_adapters.OverloadOrder(stub_960)
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


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_read_marc_file(stub_bib, library):
    bib_file = io.BytesIO(stub_bib.as_marc())
    bib_list = [i for i in marc_adapters.read_marc_file(bib_file, library)]
    assert len(bib_list) == 1
