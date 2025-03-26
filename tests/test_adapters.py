import datetime

from overload_web.adapters import marc_adapters


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
