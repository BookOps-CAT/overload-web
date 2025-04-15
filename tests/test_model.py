from datetime import datetime

import pytest

from overload_web.domain import model


class TestBibTypes:
    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_DomainBib(self, library, order_data):
        bib = model.DomainBib(library=library, orders=[model.Order(**order_data)])
        assert bib.bib_id is None

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_DomainBib_bib_id(self, library, order_data):
        bib = model.DomainBib(
            library=library, orders=[model.Order(**order_data)], bib_id="b123456789"
        )
        assert bib.bib_id == "b123456789"

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
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


class TestOrderTypes:
    def test_Order(self, order_data):
        order = model.Order(**order_data)
        assert order.price == "$5.00"
        assert order.format == "a"
        assert order.blanket_po is None

    def test_Order_apply_template(self, template_data, order_data):
        order = model.Order(**order_data)
        template = model.Template(**template_data)
        assert order.fund == "25240adbk"
        order.apply_template(template)
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
        assert template.primary_matchpoint == "isbn"
        assert template.secondary_matchpoint is None
        assert template.tertiary_matchpoint is None
        assert template.agent is None
        assert template.id is None
        assert template.name is None
        assert template.matchpoints == ["isbn"]

    def test_Template_no_input(self):
        template = model.Template()
        attr_vals = [v for k, v in template.__dict__.items()]
        assert all(i is None for i in attr_vals) is True
        assert template.primary_matchpoint is None
        assert template.secondary_matchpoint is None
        assert template.tertiary_matchpoint is None
        assert template.matchpoints == []

    def test_Template_positional_args(self):
        with pytest.raises(TypeError) as exc:
            model.Template("a", None, "7", "xxu", datetime(2024, 1, 1), "a")
        assert (
            str(exc.value)
            == "Template.__init__() takes 1 positional argument but 7 were given"
        )
