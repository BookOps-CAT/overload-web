import datetime

import pytest

from overload_web.domain import model


@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestDomainBib:
    def test_DomainBib(self, library, order_data):
        bib = model.DomainBib(library=library, orders=[model.Order(**order_data)])
        assert bib.bib_id is None

    def test_DomainBib_from_marc(self, library, stub_bib):
        bib = model.DomainBib.from_marc(bib=stub_bib)
        assert bib.bib_id is None
        assert bib.isbn == "9781234567890"
        assert bib.oclc_number == []
        assert len(bib.orders) == 1
        assert bib.orders[0].create_date == datetime.date(2025, 1, 1)
        assert bib.orders[0].blanket_po == "baz"

    def test_DomainBib_from_marc_no_961(self, library, stub_bib):
        stub_bib.remove_fields("961")
        bib = model.DomainBib.from_marc(bib=stub_bib)
        assert bib.bib_id is None
        assert bib.isbn == "9781234567890"
        assert bib.oclc_number == []
        assert len(bib.orders) == 1
        assert bib.orders[0].create_date == datetime.date(2025, 1, 1)
        assert bib.orders[0].blanket_po is None

    def test_DomainBib_bib_id(self, library, order_data):
        bib = model.DomainBib(
            library=library, orders=[model.Order(**order_data)], bib_id="b123456789"
        )
        assert bib.bib_id == "b123456789"

    def test_DomainBib_apply_template(self, library, order_data, template_data):
        bib = model.DomainBib(library=library, orders=[model.Order(**order_data)])
        assert bib.orders[0].fund == "25240adbk"
        bib.apply_template(template_data=template_data)
        assert bib.orders[0].fund == "10001adbk"


class TestMatchpoints:
    def test_Matchpoints(self):
        matchpoints = model.Matchpoints(primary="isbn", secondary="oclc_number")
        assert matchpoints.primary == "isbn"
        assert matchpoints.secondary == "oclc_number"
        assert matchpoints.tertiary is None
        assert matchpoints.as_list() == ["isbn", "oclc_number"]

    def test_Matchpoints_default(self):
        matchpoints = model.Matchpoints()
        assert matchpoints.primary is None
        assert matchpoints.secondary is None
        assert matchpoints.tertiary is None

    def test_Matchpoints_positional(self):
        matchpoints_1 = model.Matchpoints("isbn", "upc", "issn")
        matchpoints_2 = model.Matchpoints("isbn", "issn")
        assert matchpoints_1.primary == "isbn"
        assert matchpoints_1.secondary == "upc"
        assert matchpoints_1.tertiary == "issn"
        assert matchpoints_2.primary == "isbn"
        assert matchpoints_2.secondary == "issn"
        assert matchpoints_2.tertiary is None

    def test_Matchpoints_eq_not_implemented(self):
        matchpoints = model.Matchpoints("isbn", "upc")
        assert matchpoints == model.Matchpoints(primary="isbn", secondary="upc")
        assert matchpoints != model.Matchpoints("isbn", "issn")
        assert matchpoints.__eq__("foo") is NotImplemented

    def test_Matchpoints_value_error_kw(self):
        with pytest.raises(ValueError) as exc:
            model.Matchpoints(primary="isbn", tertiary="upc")
        assert str(exc.value) == "Cannot have tertiary matchpoint without secondary."

    def test_Matchpoints_value_error_positional(self):
        with pytest.raises(ValueError) as exc:
            model.Matchpoints("isbn", tertiary="upc")
        assert str(exc.value) == "Cannot have tertiary matchpoint without secondary."


class TestOrder:
    def test_Order(self, order_data):
        order = model.Order(**order_data)
        assert order.price == "$5.00"
        assert order.format == "a"
        assert order.blanket_po is None

    def test_Order_apply_template(self, template_data, order_data):
        order = model.Order(**order_data)
        assert order.fund == "25240adbk"
        order.apply_template(template_data)
        assert order.fund == "10001adbk"


class TestTemplate:
    def test_Template(self, template_data):
        template = model.Template(**template_data)
        assert template.create_date == "2024-01-01"
        assert template.price == "$20.00"
        assert template.fund == "10001adbk"
        assert template.copies == "5"
        assert template.lang == "spa"
        assert template.country == "xxu"
        assert template.vendor_code == "0049"
        assert template.format == "a"
        assert template.order_code_1 == "b"
        assert template.order_code_2 is None
        assert template.order_code_3 == "d"
        assert template.order_code_4 == "a"
        assert template.selector_note is None
        assert template.order_type == "p"
        assert template.status == "o"
        assert template.internal_note == "foo"
        assert template.var_field_isbn is None
        assert template.vendor_notes == "bar"
        assert template.vendor_title_no is None
        assert template.blanket_po is None

    def test_Template_no_input(self):
        template = model.Template()
        attr_vals = [v for k, v in template.__dict__.items() if k != "matchpoints"]
        assert all(i is None for i in attr_vals) is True
        assert list(template.matchpoints.__dict__.values()) == [None, None, None]

    def test_Template_positional_args(self):
        with pytest.raises(TypeError) as exc:
            model.Template("a", None, "7", "xxu", datetime.datetime(2024, 1, 1), "a")
        assert (
            str(exc.value)
            == "Template.__init__() takes 1 positional argument but 7 were given"
        )
