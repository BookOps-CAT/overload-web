from datetime import datetime

import pytest

from overload_web.domain import model


class TestOrderTypes:
    def test_Order(self):
        order = model.Order(
            create_date=datetime(2024, 1, 1),
            locations=["(4)fwa0f", "(2)bca0f", "gka0f"],
            price="$5.00",
            fund="25240adbk",
            copies="7",
            lang="eng",
            country="xxu",
            vendor_code="0049",
            format="a",
            selector="b",
            selector_note=None,
            audience="a",
            source="d",
            order_type="p",
            status="o",
            internal_note=None,
            var_field_isbn=None,
            vendor_notes=None,
            vendor_title_no=None,
            blanket_po=None,
        )
        assert order.price == "$5.00"
        assert order.format == "a"
        assert order.blanket_po is None

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OrderBib(self, library, stub_order):
        bib = model.OrderBib(library=library, orders=[stub_order])
        assert bib.bib_id is None

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_OrderBib_bib_id(self, library, stub_order):
        order = stub_order
        bib = model.OrderBib(library=library, orders=[order], bib_id="b123456789")
        assert bib.bib_id == "b123456789"

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_model_apply_template(self, library, stub_template, stub_order):
        bib = model.OrderBib(library=library, orders=[stub_order])
        assert bib.orders[0].fund == "25240adbk"
        updated_bib = model.apply_template(bib, stub_template)
        assert updated_bib.orders[0].fund == "10001adbk"


class TestTemplateTypes:
    def test_Template(self):
        template = model.Template(
            audience="a",
            blanket_po=None,
            copies="7",
            country="xxu",
            create_date=datetime(2024, 1, 1),
            format="a",
            fund="25240adbk",
            internal_note=None,
            lang="eng",
            order_type="p",
            price="$5.00",
            selector="b",
            selector_note=None,
            source="d",
            status="o",
            var_field_isbn=None,
            vendor_code="0049",
            vendor_notes=None,
            vendor_title_no=None,
            primary_matchpoint=None,
            secondary_matchpoint=None,
            tertiary_matchpoint=None,
        )
        assert template.create_date == datetime(2024, 1, 1)
        assert template.price == "$5.00"
        assert template.fund == "25240adbk"
        assert template.copies == "7"
        assert template.lang == "eng"
        assert template.country == "xxu"
        assert template.vendor_code == "0049"
        assert template.format == "a"
        assert template.selector == "b"
        assert template.selector_note is None
        assert template.audience == "a"
        assert template.source == "d"
        assert template.order_type == "p"
        assert template.status == "o"
        assert template.internal_note is None
        assert template.var_field_isbn is None
        assert template.vendor_notes is None
        assert template.vendor_title_no is None
        assert template.blanket_po is None
        assert template.primary_matchpoint is None
        assert template.secondary_matchpoint is None
        assert template.tertiary_matchpoint is None
        assert template.matchpoints == []

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

    def test_PersistentTemplate(self, stub_template):
        template_data = stub_template.__dict__
        template_data["id"] = 1
        template_data["name"] = "Foo Vendor Template"
        template_data["agent"] = "user"
        template = model.PersistentTemplate(**template_data)
        assert template.audience == "a"
        assert template.blanket_po is None
        assert template.copies == "5"
        assert template.country == "xxu"
        assert template.create_date == "2024-01-01"
        assert template.format == "a"
        assert template.fund == "10001adbk"
        assert template.internal_note == "foo"
        assert template.lang == "spa"
        assert template.order_type == "p"
        assert template.price == "$20.00"
        assert template.selector == "b"
        assert template.selector_note is None
        assert template.source == "d"
        assert template.status == "o"
        assert template.var_field_isbn is None
        assert template.vendor_code == "0049"
        assert template.vendor_notes == "bar"
        assert template.vendor_title_no is None
        assert template.primary_matchpoint == "isbn"
        assert template.secondary_matchpoint is None
        assert template.tertiary_matchpoint is None
        assert template.id == 1
        assert template.name == "Foo Vendor Template"
        assert template.agent == "user"

    def test_PersistentTemplate_required_vars(self):
        template = model.PersistentTemplate(id=2, name="Template", agent="user")
        attr_vals = [v for k, v in template.__dict__.items() if v]
        assert attr_vals == [2, "Template", "user"]

    def test_PersistentTemplate_missing_vars(self, stub_template):
        template_data = stub_template.__dict__
        with pytest.raises(TypeError) as exc:
            model.PersistentTemplate(**template_data)
        assert (
            str(exc.value)
            == "PersistentTemplate.__init__() missing 3 required keyword-only arguments: 'id', 'name', and 'agent'"
        )

    def test_PersistentTemplate_positional_args(self):
        with pytest.raises(TypeError) as exc:
            model.PersistentTemplate("a", None, "7", "xxu", datetime(2024, 1, 1), "a")
        assert (
            str(exc.value)
            == "PersistentTemplate.__init__() takes 1 positional argument but 7 were given"
        )
