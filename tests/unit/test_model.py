import pytest

from overload_web.domain_models import bibs, responses
from overload_web.files.domain import vendor_files


class TestBibId:
    @pytest.mark.parametrize("value", ["b123456789", ".b123456789"])
    def test_BibId(self, value):
        bib_id = bibs.BibId(value=value)
        assert str(bib_id) == value
        assert repr(bib_id) == f"BibId(value='{value}')"

    def test_BibId_invalid(self):
        with pytest.raises(ValueError) as exc:
            bibs.BibId(value=123456789)
        assert str(exc.value) == "BibId must be a non-empty string."


class TestContext:
    @pytest.mark.parametrize("value", ["BL", "RL"])
    def test_Collection(self, value):
        collection = bibs.Collection(value)
        assert str(collection) == value
        assert bibs.Collection.BRANCH.value == "BL"
        assert bibs.Collection.BRANCH.name == "BRANCH"
        assert bibs.Collection.RESEARCH.value == "RL"
        assert bibs.Collection.RESEARCH.name == "RESEARCH"

    def test_Collection_invalid(self):
        with pytest.raises(ValueError) as exc:
            bibs.Collection("foo")
        assert str(exc.value) == "'foo' is not a valid Collection"

    @pytest.mark.parametrize("value", ["bpl", "nypl"])
    def test_LibrarySystem(self, value):
        library = bibs.LibrarySystem(value)
        assert str(library) == value
        assert bibs.LibrarySystem.BPL.value == "bpl"
        assert bibs.LibrarySystem.BPL.name == "BPL"
        assert bibs.LibrarySystem.NYPL.value == "nypl"
        assert bibs.LibrarySystem.NYPL.name == "NYPL"

    def test_LibrarySystem_invalid(self):
        with pytest.raises(ValueError) as exc:
            bibs.LibrarySystem("foo")
        assert str(exc.value) == "'foo' is not a valid LibrarySystem"

    @pytest.mark.parametrize("value", ["full", "order_level"])
    def test_RecordType(self, value):
        record_type = bibs.RecordType(value)
        assert str(record_type) == value
        assert bibs.RecordType.FULL.value == "full"
        assert bibs.RecordType.FULL.name == "FULL"
        assert bibs.RecordType.ORDER_LEVEL.value == "order_level"
        assert bibs.RecordType.ORDER_LEVEL.name == "ORDER_LEVEL"

    def test_RecordType_invalid(self):
        with pytest.raises(ValueError) as exc:
            bibs.RecordType("foo")
        assert str(exc.value) == "'foo' is not a valid RecordType"


@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestDomainBib:
    def test_DomainBib(self, library, order_data):
        bib = bibs.DomainBib(library=library, orders=[bibs.Order(**order_data)])
        assert bib.bib_id is None

    def test_DomainBib_bib_id(self, library, order_data):
        bib = bibs.DomainBib(
            library=library,
            orders=[bibs.Order(**order_data)],
            bib_id="b123456789",
        )
        assert str(bib.bib_id) == "b123456789"

    def test_DomainBib_apply_order_template(self, library, order_data, template_data):
        bib = bibs.DomainBib(library=library, orders=[bibs.Order(**order_data)])
        assert bib.orders[0].fund == "25240adbk"
        bib.apply_order_template(template_data=template_data)
        assert bib.orders[0].fund == "10001adbk"


class TestOrder:
    def test_Order(self, order_data):
        order = bibs.Order(**order_data)
        assert order.price == "$5.00"
        assert order.format == "a"
        assert order.blanket_po is None
        assert order.locations == ["(4)fwa0f", "(2)bca0f", "gka0f"]
        assert order.shelves == ["0f", "0f", "0f"]
        assert order.audience == ["a", "a", "a"]
        assert order.branches == ["fw", "bc", "gk"]

    def test_Order_apply_template(self, template_data, order_data):
        order = bibs.Order(**order_data)
        assert order.fund == "25240adbk"
        order.apply_template(template_data)
        assert order.fund == "10001adbk"


class TestOrderId:
    @pytest.mark.parametrize("value", ["123456789", ".o123456789"])
    def test_OrderId(self, value):
        order_id = bibs.OrderId(value=value)
        assert str(order_id) == value
        assert repr(order_id) == f"OrderId(value='{value}')"

    def test_OrderId_invalid(self):
        with pytest.raises(ValueError) as exc:
            bibs.OrderId(value=987654321)
        assert str(exc.value) == "OrderId must be a non-empty string."


class TestVendorFile:
    def test_VendorFile(self):
        file = vendor_files.VendorFile(id="foo", content=b"", file_name="bar.mrc")
        assert file.id == "foo"
        assert hasattr(file.content, "hex")
        assert file.file_name == "bar.mrc"

    def test_VendorFile_create(self):
        file = vendor_files.VendorFile.create(content=b"", file_name="bar.mrc")
        assert isinstance(file.id, vendor_files.VendorFileId)
        assert repr(file.id) == f"VendorFileId(value='{str(file.id)}')"

    def test_VendorFileId_new(self):
        id = vendor_files.VendorFileId.new()
        assert isinstance(id, vendor_files.VendorFileId)
        assert repr(id) == f"VendorFileId(value='{str(id)}')"

    def test_VendorFileId_invalid(self):
        with pytest.raises(ValueError) as exc:
            vendor_files.VendorFileId(value=123)
        assert str(exc.value) == "VendorFileId must be a non-empty string."


class TestSierraResponses:
    BASE_RESPONSE = {"id": "1234567890", "title": "Foo"}

    def test_nypl_response_bl(self):
        data = {
            "varFields": [
                {
                    "marcTag": "091",
                    "subfields": [
                        {"tag": "a", "content": "FIC"},
                        {"tag": "c", "content": "BAR"},
                    ],
                },
                {
                    "marcTag": "901",
                    "subfields": [{"tag": "b", "content": "CATBL"}],
                },
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "BL"}],
                },
                {
                    "marcTag": "020",
                    "subfields": [{"tag": "a", "content": "9781234567890"}],
                },
                {
                    "marcTag": "024",
                    "subfields": [{"tag": "a", "content": "12345"}],
                },
                {
                    "marcTag": "028",
                    "subfields": [{"tag": "a", "content": "67890"}],
                },
                {
                    "marcTag": "035",
                    "subfields": [{"tag": "a", "content": "(OCoLC)9876543210)"}],
                },
            ],
            "standardNumbers": ["9781234567890"],
            "controlNumber": ["on9876543210"],
            "updatedDate": "2020-01-01T00:00:01",
            **self.BASE_RESPONSE,
        }
        response = responses.NYPLPlatformResponse(data)
        assert response.cat_source == "inhouse"
        assert response.collection == "BL"

    def test_nypl_response_rl(self):
        data = {
            "varFields": [
                {
                    "marcTag": "852",
                    "ind1": "8",
                    "subfields": [{"tag": "a", "content": "ReCAP 20-123456"}],
                },
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "RL"}],
                },
            ],
            **self.BASE_RESPONSE,
        }
        response = responses.NYPLPlatformResponse(data)
        assert response.cat_source == "vendor"
        assert response.collection == "RL"

    def test_nypl_response_mixed(self):
        data = {
            "varFields": [
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "RL"}],
                },
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "BL"}],
                },
            ],
            **self.BASE_RESPONSE,
        }
        response = responses.NYPLPlatformResponse(data)
        assert response.cat_source == "vendor"
        assert response.collection == "MIXED"

    @pytest.mark.parametrize(
        "field, collection",
        [({"marcTag": "091"}, "BL"), ({"marcTag": "852", "ind1": "8"}, "RL")],
    )
    def test_nypl_response_call_number_check(self, field, collection):
        field["subfields"] = [{"tag": "a", "content": "Foo"}]
        data = {"varFields": [field], **self.BASE_RESPONSE}
        response = responses.NYPLPlatformResponse(data)
        assert response.collection == collection

    def test_nypl_response_call_number_mixed(self):
        data = {
            "varFields": [
                {
                    "marcTag": "852",
                    "ind1": "8",
                    "subfields": [{"tag": "a", "content": "ReCAP 20-123456"}],
                },
                {"marcTag": "091", "subfields": [{"tag": "a", "content": "FIC"}]},
            ],
            **self.BASE_RESPONSE,
        }
        response = responses.NYPLPlatformResponse(data)
        assert response.collection == "MIXED"

    def test_bpl_response(self):
        data = {
            "sm_item_data": ['{"barcode": "333331234567890"}'],
            "ss_marc_tag_001": "on9876543210",
            "ss_marc_tag_003": "OCoLC",
            "ss_marc_tag_005": "20200101000001.0",
            "sm_bib_varfields": [
                "005 || 20200101000001.0",
                "020 || {{a}} 9781234567890",
                "024 || {{a}} 12345",
                "028 || {{a}} 67890",
                "035 || {{a}} (OCoLC)9876543210",
                "099 || {{a}} FIC || {{a}} BAR",
            ],
            "isbn": ["9781234567890"],
            "call_number": "FIC BAR",
            **self.BASE_RESPONSE,
        }
        response = responses.BPLSolrResponse(data)
        assert response.barcodes == ["333331234567890"]
        assert response.branch_call_number == ["FIC BAR"]
        assert response.cat_source == "inhouse"
        assert len(response.var_fields) == 5
