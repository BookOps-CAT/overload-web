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
