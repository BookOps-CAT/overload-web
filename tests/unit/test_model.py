import datetime

import pytest

from overload_web.domain import models


class TestBibId:
    @pytest.mark.parametrize("value", ["b123456789", ".b123456789"])
    def test_BibId(self, value):
        bib_id = models.bibs.BibId(value=value)
        assert str(bib_id) == value
        assert repr(bib_id) == f"BibId(value='{value}')"

    def test_BibId_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.bibs.BibId(value=123456789)
        assert str(exc.value) == "BibId must be a non-empty string."


class TestContext:
    @pytest.mark.parametrize("value", ["BL", "RL"])
    def test_Collection(self, value):
        collection = models.bibs.Collection(value)
        assert str(collection) == value
        assert models.bibs.Collection.BRANCH.value == "BL"
        assert models.bibs.Collection.BRANCH.name == "BRANCH"
        assert models.bibs.Collection.RESEARCH.value == "RL"
        assert models.bibs.Collection.RESEARCH.name == "RESEARCH"

    def test_Collection_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.bibs.Collection("foo")
        assert str(exc.value) == "'foo' is not a valid Collection"

    @pytest.mark.parametrize("value", ["bpl", "nypl"])
    def test_LibrarySystem(self, value):
        library = models.bibs.LibrarySystem(value)
        assert str(library) == value
        assert models.bibs.LibrarySystem.BPL.value == "bpl"
        assert models.bibs.LibrarySystem.BPL.name == "BPL"
        assert models.bibs.LibrarySystem.NYPL.value == "nypl"
        assert models.bibs.LibrarySystem.NYPL.name == "NYPL"

    def test_LibrarySystem_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.bibs.LibrarySystem("foo")
        assert str(exc.value) == "'foo' is not a valid LibrarySystem"

    @pytest.mark.parametrize("value", ["full", "order_level"])
    def test_RecordType(self, value):
        record_type = models.bibs.RecordType(value)
        assert str(record_type) == value
        assert models.bibs.RecordType.FULL.value == "full"
        assert models.bibs.RecordType.FULL.name == "FULL"
        assert models.bibs.RecordType.ORDER_LEVEL.value == "order_level"
        assert models.bibs.RecordType.ORDER_LEVEL.name == "ORDER_LEVEL"

    def test_RecordType_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.bibs.RecordType("foo")
        assert str(exc.value) == "'foo' is not a valid RecordType"


@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestDomainBib:
    def test_DomainBib(self, library, order_data):
        bib = models.bibs.DomainBib(
            library=library, orders=[models.bibs.Order(**order_data)]
        )
        assert bib.bib_id is None

    def test_DomainBib_from_marc(self, library, stub_bib):
        bib = models.bibs.DomainBib.from_marc(bib=stub_bib)
        assert bib.bib_id is None
        assert bib.isbn == "9781234567890"
        assert bib.oclc_number == []
        assert len(bib.orders) == 1
        assert bib.orders[0].create_date == datetime.date(2025, 1, 1)
        assert bib.orders[0].blanket_po == "baz"
        assert bib.call_number is None
        assert bib.barcodes == ["333331234567890"]

    def test_DomainBib_from_marc_no_961(self, library, stub_bib):
        stub_bib.remove_fields("961")
        bib = models.bibs.DomainBib.from_marc(bib=stub_bib)
        assert bib.bib_id is None
        assert bib.isbn == "9781234567890"
        assert bib.oclc_number == []
        assert len(bib.orders) == 1
        assert bib.orders[0].create_date == datetime.date(2025, 1, 1)
        assert bib.orders[0].blanket_po is None

    def test_DomainBib_bib_id(self, library, order_data):
        bib = models.bibs.DomainBib(
            library=library,
            orders=[models.bibs.Order(**order_data)],
            bib_id="b123456789",
        )
        assert bib.bib_id == "b123456789"

    def test_DomainBib_apply_template(self, library, order_data, template_data):
        bib = models.bibs.DomainBib(
            library=library, orders=[models.bibs.Order(**order_data)]
        )
        assert bib.orders[0].fund == "25240adbk"
        bib.apply_template(template_data=template_data)
        assert bib.orders[0].fund == "10001adbk"


class TestMatchpoints:
    def test_Matchpoints(self):
        matchpoints = models.templates.Matchpoints(
            primary="isbn", secondary="oclc_number"
        )
        assert matchpoints.primary == "isbn"
        assert matchpoints.secondary == "oclc_number"
        assert matchpoints.tertiary is None
        assert matchpoints.as_list() == ["isbn", "oclc_number"]

    def test_Matchpoints_default(self):
        matchpoints = models.templates.Matchpoints()
        assert matchpoints.primary is None
        assert matchpoints.secondary is None
        assert matchpoints.tertiary is None

    def test_Matchpoints_positional(self):
        matchpoints_1 = models.templates.Matchpoints("isbn", "upc", "issn")
        matchpoints_2 = models.templates.Matchpoints("isbn", "issn")
        assert matchpoints_1.primary == "isbn"
        assert matchpoints_1.secondary == "upc"
        assert matchpoints_1.tertiary == "issn"
        assert matchpoints_2.primary == "isbn"
        assert matchpoints_2.secondary == "issn"
        assert matchpoints_2.tertiary is None

    def test_Matchpoints_eq_not_implemented(self):
        matchpoints = models.templates.Matchpoints("isbn", "upc")
        assert matchpoints == models.templates.Matchpoints(
            primary="isbn", secondary="upc"
        )
        assert matchpoints != models.templates.Matchpoints("isbn", "issn")
        assert matchpoints.__eq__("foo") is NotImplemented

    def test_Matchpoints_value_error_kw(self):
        with pytest.raises(ValueError) as exc:
            models.templates.Matchpoints(primary="isbn", tertiary="upc")
        assert str(exc.value) == "Cannot have tertiary matchpoint without secondary."

    def test_Matchpoints_value_error_positional(self):
        with pytest.raises(ValueError) as exc:
            models.templates.Matchpoints("isbn", tertiary="upc")
        assert str(exc.value) == "Cannot have tertiary matchpoint without secondary."

    def test_Matchpoints_value_error_too_many(self):
        with pytest.raises(ValueError) as exc:
            models.templates.Matchpoints("isbn", "upc", "issn", "oclc_number")
        assert (
            str(exc.value) == "Matchpoints should be passed no more than three values."
        )


class TestOrder:
    def test_Order(self, order_data):
        order = models.bibs.Order(**order_data)
        assert order.price == "$5.00"
        assert order.format == "a"
        assert order.blanket_po is None
        assert order.locations == ["(4)fwa0f", "(2)bca0f", "gka0f"]
        assert order.shelves == ["0f", "0f", "0f"]
        assert order.audience == ["a", "a", "a"]
        assert order.branches == ["fw", "bc", "gk"]

    def test_Order_apply_template(self, template_data, order_data):
        order = models.bibs.Order(**order_data)
        assert order.fund == "25240adbk"
        order.apply_template(template_data)
        assert order.fund == "10001adbk"


class TestOrderId:
    @pytest.mark.parametrize("value", ["123456789", ".o123456789"])
    def test_OrderId(self, value):
        order_id = models.bibs.OrderId(value=value)
        assert str(order_id) == value
        assert repr(order_id) == f"OrderId(value='{value}')"

    def test_OrderId_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.bibs.OrderId(value=987654321)
        assert str(exc.value) == "OrderId must be a non-empty string."


class TestTemplate:
    def test_Template(self, template_data):
        template_obj = models.templates.Template(**template_data)
        assert template_obj.create_date == "2024-01-01"
        assert template_obj.price == "$20.00"
        assert template_obj.fund == "10001adbk"
        assert template_obj.copies == "5"
        assert template_obj.lang == "spa"
        assert template_obj.country == "xxu"
        assert template_obj.vendor_code == "0049"
        assert template_obj.format == "a"
        assert template_obj.order_code_1 == "b"
        assert template_obj.order_code_2 is None
        assert template_obj.order_code_3 == "d"
        assert template_obj.order_code_4 == "a"
        assert template_obj.selector_note is None
        assert template_obj.order_type == "p"
        assert template_obj.status == "o"
        assert template_obj.internal_note == "foo"
        assert template_obj.var_field_isbn is None
        assert template_obj.vendor_notes == "bar"
        assert template_obj.vendor_title_no is None
        assert template_obj.blanket_po is None

    def test_Template_no_input(self):
        template_obj = models.templates.Template()
        attr_vals = [v for k, v in template_obj.__dict__.items() if k != "matchpoints"]
        assert all(i is None for i in attr_vals) is True
        assert list(template_obj.matchpoints.__dict__.values()) == [None, None, None]

    def test_Template_positional_args(self):
        with pytest.raises(TypeError) as exc:
            models.templates.Template(
                "a", None, "7", "xxu", datetime.datetime(2024, 1, 1), "a"
            )
        assert (
            str(exc.value)
            == "Template.__init__() takes 1 positional argument but 7 were given"
        )


class TestTemplateId:
    @pytest.mark.parametrize("value", ["123", "456"])
    def test_TemplateId(self, value):
        template_id = models.templates.TemplateId(value=value)
        assert str(template_id) == value
        assert repr(template_id) == f"TemplateId(value='{value}')"

    def test_TemplateId_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.templates.TemplateId(value=123)
        assert str(exc.value) == "TemplateId must be a non-empty string."


class TestVendorFile:
    def test_VendorFile(self):
        file = models.files.VendorFile(id="foo", content=b"", file_name="bar.mrc")
        assert file.id == "foo"
        assert hasattr(file.content, "hex")
        assert file.file_name == "bar.mrc"

    def test_VendorFile_create(self):
        file = models.files.VendorFile.create(content=b"", file_name="bar.mrc")
        assert isinstance(file.id, models.files.VendorFileId)
        assert repr(file.id) == f"VendorFileId(value='{str(file.id)}')"

    def test_VendorFileId_new(self):
        id = models.files.VendorFileId.new()
        assert isinstance(id, models.files.VendorFileId)
        assert repr(id) == f"VendorFileId(value='{str(id)}')"

    def test_VendorFileId_invalid(self):
        with pytest.raises(ValueError) as exc:
            models.files.VendorFileId(value=123)
        assert str(exc.value) == "VendorFileId must be a non-empty string."
