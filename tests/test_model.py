from datetime import datetime

import pytest

from overload_web.domain import model


@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestBibTypes:
    def test_DomainBib(self, library, order_data):
        bib = model.DomainBib(library=library, orders=[model.Order(**order_data)])
        assert bib.bib_id is None

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

    @pytest.mark.parametrize(
        "matchpoints, result",
        [(["isbn"], "123"), (["oclc_number"], "234"), (["isbn", "oclc_number"], "345")],
    )
    def test_DomainBib_match(
        self, library, order_data, make_domain_bib, matchpoints, result
    ):
        bib = model.DomainBib(
            library=library,
            orders=[model.Order(**order_data)],
            isbn="9781234567890",
            oclc_number="123456789",
            upc=None,
        )
        assert bib.bib_id is None

        bib_1 = make_domain_bib({"bib_id": "123", "isbn": "9781234567890"})
        bib_2 = make_domain_bib(
            {"bib_id": "234", "isbn": "1234567890", "oclc_number": "123456789"}
        )
        bib_3 = make_domain_bib(
            {"bib_id": "345", "isbn": "9781234567890", "oclc_number": "123456789"}
        )
        bib_4 = make_domain_bib({"bib_id": "456", "upc": "333"})
        bib.match(bibs=[bib_1, bib_2, bib_3, bib_4], matchpoints=matchpoints)
        assert bib.bib_id == result


class TestMatchpointsTypes:
    def test_Matchpoints(self):
        matchpoints = model.Matchpoints(primary="isbn", secondary="oclc_number")
        assert matchpoints.primary == "isbn"
        assert matchpoints.secondary == "oclc_number"
        assert matchpoints.tertiary is None

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


class TestOrderTypes:
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


class TestTemplateTypes:
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
        assert template.selector == "b"
        assert template.selector_note is None
        assert template.audience == "a"
        assert template.source == "d"
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
            model.Template("a", None, "7", "xxu", datetime(2024, 1, 1), "a")
        assert (
            str(exc.value)
            == "Template.__init__() takes 1 positional argument but 7 were given"
        )
