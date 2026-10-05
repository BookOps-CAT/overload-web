import datetime
import random

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.pvf import models, services
from overload_web.infrastructure import marc_handler


@pytest.fixture
def create_marc_record():
    def create_marc(library, collection):
        bib = Bib()
        bib.leader = "00000cam  2200517 i 4500"
        bib.library = library
        bib.add_field(Field(tag="005", data="20000101010001.0"))
        bib.add_field(
            Field(
                tag="020",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="9781234567890")],
            )
        )
        if library == "bpl":
            bib.add_field(
                Field(
                    tag="037",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value="123"),
                        Subfield(code="b", value="OverDrive, Inc."),
                    ],
                )
            )
            bib.add_field(
                Field(
                    tag="099",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value="Foo")],
                )
            )
        else:
            if collection == "BL":
                bib.add_field(
                    Field(
                        tag="091",
                        indicators=Indicators(" ", " "),
                        subfields=[Subfield(code="a", value="Foo")],
                    )
                )
            else:
                bib.add_field(
                    Field(
                        tag="852",
                        indicators=Indicators("8", " "),
                        subfields=[Subfield(code="a", value="Foo")],
                    )
                )
            bib.add_field(
                Field(
                    tag="910",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=collection)],
                )
            )
        bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", "1"),
                subfields=[Subfield(code="i", value="333331234567890")],
            )
        )
        bib.add_field(
            Field(
                tag="960",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="l"),
                    Subfield(code="b", value="-"),
                    Subfield(code="c", value="j"),
                    Subfield(code="d", value="c"),
                    Subfield(code="e", value="d"),
                    Subfield(code="f", value="a"),
                    Subfield(code="g", value="b"),
                    Subfield(code="h", value="-"),
                    Subfield(code="i", value="l"),
                    Subfield(code="j", value="-"),
                    Subfield(code="k", value="A01"),
                    Subfield(code="m", value="o"),
                    Subfield(code="n", value="-"),
                    Subfield(code="o", value="13"),
                    Subfield(code="p", value="  -  -  "),
                    Subfield(code="q", value="01-01-25"),
                    Subfield(code="r", value="  -  -  "),
                    Subfield(code="s", value="{{dollar}}13.20"),
                    Subfield(code="t", value="agj0y"),
                    Subfield(code="u", value="lease"),
                    Subfield(code="v", value="btlea"),
                    Subfield(code="w", value="eng"),
                    Subfield(code="x", value="xxu"),
                    Subfield(code="y", value="1"),
                    Subfield(code="z", value=".o10000010"),
                ],
            )
        )
        bib.add_field(
            Field(
                tag="961",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="d", value="foo"),
                    Subfield(code="f", value="bar"),
                    Subfield(code="m", value="baz"),
                ],
            )
        )
        return bib

    return create_marc


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc(request, create_marc_record) -> Bib:
    return create_marc_record(request.param[0], request.param[1])


@pytest.fixture
def stub_marc(request, create_marc_record) -> Bib:
    marker = request.node.get_closest_marker("workflow")
    return create_marc_record(marker.kwargs["library"], marker.kwargs["collection"])


@pytest.fixture
def stub_full_bib(stub_bib):
    def create_bib(library, collection, control_number, item_tag):
        number = random.randint(0, 100)
        barcode = f"33333{str(number).zfill(10)}"
        if item_tag == "960":
            field_037b = "Foo"
            item_ind2 = " "
        else:
            field_037b = "OverDrive, Inc."
            item_ind2 = "1"
        field_list = [
            {
                "tag": "037",
                "ind1": " ",
                "ind2": " ",
                "subfields": [
                    {"code": "a", "value": "123"},
                    {"code": "b", "value": field_037b},
                ],
            },
            {
                "tag": item_tag,
                "ind1": " ",
                "ind2": item_ind2,
                "subfields": [{"code": "i", "value": barcode}],
            },
            {
                "tag": "949",
                "ind1": " ",
                "ind2": " ",
                "subfields": [{"code": "a", "value": "*b2=a;"}],
            },
        ]
        parsed_fields = []
        bib = Bib()
        bib.leader = "00000cam  2200517 i 4500"
        bib.library = library
        for field in field_list:
            bib.add_field(
                Field(
                    tag=field["tag"],
                    indicators=(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=i["code"], value=i["value"])
                        for i in field["subfields"]
                    ],
                )
            )
            parsed_fields.append(
                models.ParsedField(
                    tag=field["tag"],
                    indicators=(field["ind1"], field["ind2"]),
                    subfields=[
                        models.ParsedSubfield(code=i["code"], value=i["value"])
                        for i in field["subfields"]
                    ],
                )
            )
        domain_bib = stub_bib(library, collection, "cat")
        domain_bib.binary_data = bib.as_marc()
        domain_bib.parsed_fields = parsed_fields
        domain_bib.barcodes = [barcode]
        domain_bib.control_number = control_number
        domain_bib.action = "insert"
        return domain_bib

    return create_bib


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def full_bib_949_item(stub_full_bib, request):
    def create_bib(control_number):
        return stub_full_bib(request.param[0], request.param[1], control_number, "949")

    return create_bib


@pytest.fixture
def full_bib_960_item(stub_full_bib):
    def create_bib(control_number):
        return stub_full_bib("bpl", None, control_number, "960")

    return create_bib


@pytest.fixture
def stub_reviewer():
    return services.BibReviewer(handler=marc_handler.MarcUpdater())


class TestMarcParser:
    ENGINE = marc_handler.MarcParser()

    def test_get_reader(self, mock_marc):
        combined = self.ENGINE.get_reader(
            library=mock_marc.library, data=mock_marc.as_marc()
        )
        assert len([i for i in combined]) >= 1

    def test_identify_vendor(self, mock_marc, get_constants):
        vendor_mapping = get_constants["parsing_rules"]["vendor_mapping"]
        vendor_info = self.ENGINE.identify_vendor(obj=mock_marc, mapping=vendor_mapping)
        assert list(vendor_info.keys()) == [
            "name",
            "vendor_tags",
            "matchpoints",
            "bib_fields",
        ]
        assert vendor_info["name"] == "UNKNOWN"

    @pytest.mark.workflow(library="bpl", collection=None)
    @pytest.mark.parametrize(
        "field,vendor", [("B&amp;T SERIES", "BT SERIES"), ("INGRAM", "INGRAM")]
    )
    def test_identify_vendor_bpl(self, stub_marc, get_constants, field, vendor):
        vendor_mapping = get_constants["parsing_rules"]["vendor_mapping"]
        stub_marc.add_field(
            Field(
                tag="947",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=field)],
            )
        )
        vendor_info = self.ENGINE.identify_vendor(obj=stub_marc, mapping=vendor_mapping)
        assert vendor_info["name"] == vendor

    def test_map_bib_data(self, mock_marc, get_constants):
        bib_mapping = get_constants["parsing_rules"]["bib_mapping"]
        mapped = self.ENGINE.map_bib_data(obj=mock_marc, mapping=bib_mapping)
        assert list(mapped.keys()) == [
            "barcodes",
            "bib_id",
            "branch_call_number",
            "collection",
            "control_number",
            "isbn",
            "library",
            "oclc_number",
            "research_call_number",
            "title",
            "upc",
            "update_date",
            "parsed_fields",
        ]

    def test_map_order_data(self, mock_marc, get_constants):
        order_mapping = get_constants["parsing_rules"]["order_mapping"]
        mapped = self.ENGINE.map_order_data(
            obj=mock_marc.orders[0], mapping=order_mapping
        )
        assert list(mapped.keys()) == [
            "audience",
            "branches",
            "copies",
            "create_date",
            "format",
            "lang",
            "locations",
            "order_id",
            "shelves",
            "status",
            "vendor_notes",
            "order_code_1",
            "order_code_2",
            "order_code_3",
            "order_code_4",
            "order_type",
            "project_code",
            "price",
            "fund",
            "vendor_code",
            "country",
            "internal_note",
            "selector_note",
            "vendor_title_no",
            "blanket_po",
        ]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", None)]
    )
    def test_write(self, stub_bib, library, collection):
        bib = stub_bib(library, collection, "cat")
        out = self.ENGINE.write([bib.binary_data])
        assert isinstance(out, bytes)


class TestBibParser:
    ENGINE = marc_handler.MarcParser()

    @pytest.mark.workflow(record_type="cat")
    def test_combine_marc_files(self, mock_marc, get_constants, request):
        rules = get_constants["parsing_rules"]
        marker = request.node.get_closest_marker("workflow")
        record_type = marker.kwargs["record_type"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=mock_marc.library,
            collection=mock_marc.collection,
            record_type=record_type,
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        combined = parser.combine_marc_files(data=[mock_marc.as_marc()])
        assert len([i for i in combined]) > 1

    @pytest.mark.workflow(record_type="sel")
    def test_parse_marc_data_order_level_record(
        self, mock_marc, get_constants, request, caplog
    ):
        rules = get_constants["parsing_rules"]
        marker = request.node.get_closest_marker("workflow")
        record_type = marker.kwargs["record_type"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=mock_marc.library,
            collection=mock_marc.collection,
            record_type=record_type,
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        records = parser.parse_marc_data(data=mock_marc.as_marc())
        assert len(records) == 1
        assert records[0].library == mock_marc.library
        assert records[0].record_type == record_type
        assert records[0].vendor_info is None
        assert records[0].vendor == "UNKNOWN"
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.workflow(record_type="cat")
    def test_parse_marc_data_cat_record(
        self, mock_marc, get_constants, request, caplog
    ):
        rules = get_constants["parsing_rules"]
        marker = request.node.get_closest_marker("workflow")
        record_type = marker.kwargs["record_type"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=mock_marc.library,
            collection=mock_marc.collection,
            record_type=record_type,
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        records = parser.parse_marc_data(data=mock_marc.as_marc())
        assert len(records) == 1
        assert records[0].library == mock_marc.library
        assert records[0].record_type == record_type
        assert records[0].vendor_info.name == "UNKNOWN"
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg


class TestBibReviewer:
    def test_dedupe_attach(self, full_bib_949_item, stub_reviewer):
        bib = full_bib_949_item("123456789")
        bib.action = "attach"
        reviewed = stub_reviewer.review_batch(records=[bib])
        processed = stub_reviewer.deduplicate(reviewed)
        assert len(processed["NEW"]) == 0
        assert len(processed["DUP"]) == 1
        assert len(processed["DEDUPED"]) == 0

    def test_dedupe_insert(self, full_bib_949_item, stub_reviewer):
        bib = full_bib_949_item("123456789")
        reviewed = stub_reviewer.review_batch(records=[bib])
        processed = stub_reviewer.deduplicate(reviewed)
        assert len(processed["NEW"]) == 1
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 0

    def test_dedupe_combine_bibs(self, full_bib_949_item, stub_reviewer):
        bib1 = full_bib_949_item("123456789")
        bib2 = full_bib_949_item("123456789")
        reviewed = stub_reviewer.review_batch(records=[bib1, bib2])
        processed = stub_reviewer.deduplicate(reviewed)
        combined_rec = processed["DEDUPED"][0]
        deduped = Bib(combined_rec.binary_data, library=combined_rec.library)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 1
        assert sorted([i.value() for i in deduped.get_fields("949")]) == [
            "*b2=a;"
        ] + sorted(bib1.barcodes + bib2.barcodes)
        assert new_ctrl_nums == ["123456789", "123456789"]
        assert deduped_ctrl_nums == ["123456789"]

    def test_dedupe_combine_bpl_bibs(self, full_bib_960_item, stub_reviewer):
        bib1 = full_bib_960_item("123456789")
        bib2 = full_bib_960_item("123456789")
        reviewed = stub_reviewer.review_batch(records=[bib1, bib2])
        processed = stub_reviewer.deduplicate(reviewed)
        combined_rec = processed["DEDUPED"][0]
        deduped = Bib(combined_rec.binary_data, library=combined_rec.library)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 1
        assert [i.value() for i in deduped.get_fields("949")] == ["*b2=a;"]
        assert sorted([i.value() for i in deduped.get_fields("960")]) == sorted(
            bib1.barcodes + bib2.barcodes
        )
        assert new_ctrl_nums == ["123456789", "123456789"]
        assert deduped_ctrl_nums == ["123456789"]

    def test_dedupe_other_recs(self, full_bib_949_item, stub_reviewer):
        bib1a = full_bib_949_item("123456789")
        bib1b = full_bib_949_item("123456789")
        bib2 = full_bib_949_item("987654321")
        reviewed = stub_reviewer.review_batch(records=[bib1a, bib1b, bib2])
        processed = stub_reviewer.deduplicate(reviewed)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 3
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 2
        assert sorted(new_ctrl_nums) == ["123456789", "123456789", "987654321"]
        assert sorted(deduped_ctrl_nums) == ["123456789", "987654321"]

    def test_dedupe_multiple_groups(self, full_bib_949_item, stub_reviewer):
        bib_1a = full_bib_949_item("123456789")
        bib_1b = full_bib_949_item("123456789")
        bib2 = full_bib_949_item(None)
        bib3 = full_bib_949_item(None)
        bib4 = full_bib_949_item("987654321")
        bib4.control_number = "987654321"
        reviewed = stub_reviewer.review_batch(
            records=[bib_1a, bib_1b, bib2, bib3, bib4]
        )
        processed = stub_reviewer.deduplicate(reviewed)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 5
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 4
        assert new_ctrl_nums == ["123456789", "123456789", None, None, "987654321"]
        assert deduped_ctrl_nums == ["123456789", None, None, "987654321"]
