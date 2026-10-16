import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.pvf import models
from overload_web.infrastructure import marc_handler


@pytest.fixture
def stub_marc(request) -> Bib:
    marker = request.node.get_closest_marker("workflow")
    if marker:
        library = marker.kwargs["library"]
    else:
        library = "foo"
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    bib.add_field(Field(tag="005", data="20000101010001.0"))
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


class TestMarcParser:
    def test_get_reader(self, stub_marc):
        handler = marc_handler.MarcParser()
        combined = handler.get_reader(
            library=stub_marc.library, data=stub_marc.as_marc()
        )
        assert len([i for i in combined]) >= 1

    @pytest.mark.workflow(library="nypl")
    def test_identify_vendor(self, stub_marc, get_constants):
        handler = marc_handler.MarcParser()
        vendor_mapping = get_constants["parsing_rules"]["vendor_mapping"]
        vendor_info = handler.identify_vendor(obj=stub_marc, mapping=vendor_mapping)
        assert list(vendor_info.keys()) == [
            "name",
            "vendor_tags",
            "matchpoints",
            "bib_fields",
        ]
        assert vendor_info["name"] == "UNKNOWN"

    @pytest.mark.workflow(library="bpl")
    @pytest.mark.parametrize(
        "field,vendor", [("B&amp;T SERIES", "BT SERIES"), ("INGRAM", "INGRAM")]
    )
    def test_identify_vendor_alternate_tags(
        self, stub_marc, get_constants, field, vendor
    ):
        handler = marc_handler.MarcParser()
        vendor_mapping = get_constants["parsing_rules"]["vendor_mapping"]
        stub_marc.add_field(
            Field(
                tag="947",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=field)],
            )
        )
        vendor_info = handler.identify_vendor(obj=stub_marc, mapping=vendor_mapping)
        assert vendor_info["name"] == vendor

    @pytest.mark.workflow(library="nypl")
    def test_map_bib_data(self, stub_marc, get_constants):
        handler = marc_handler.MarcParser()
        bib_mapping = get_constants["parsing_rules"]["bib_mapping"]
        mapped = handler.map_bib_data(obj=stub_marc, mapping=bib_mapping)
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

    def test_map_order_data(self, stub_marc, get_constants):
        handler = marc_handler.MarcParser()
        order_mapping = get_constants["parsing_rules"]["order_mapping"]
        mapped = handler.map_order_data(obj=stub_marc.orders[0], mapping=order_mapping)
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


class TestMarcUpdater:
    def test_create_bib(self, stub_marc):
        updater = marc_handler.MarcUpdater()
        bib = updater.create_bib(
            library=stub_marc.library, binary_data=stub_marc.as_marc()
        )
        assert hasattr(bib, "control_number")

    def test_update_fields(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        original_949s = bib.get_fields("949")
        updater = marc_handler.MarcUpdater()
        updater.update_fields(
            bib=bib,
            field_updates=[
                models.MarcFieldUpdateValues(
                    tag="949",
                    ind1="",
                    ind2="",
                    subfields=[{"code": "a", "value": "*b2=a;"}],
                )
            ],
        )
        assert [i.format_field() for i in bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;",
        ]
        assert len(bib.get_fields("949")) > len(original_949s)

    def test_update_fields_delete_fields_by_tag(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        original_945s = bib.get_fields("945")
        updater = marc_handler.MarcUpdater()
        updater.update_fields(
            bib=bib,
            field_updates=[
                models.MarcFieldUpdateValues(
                    delete_fields_by_tag=True,
                    tag="945",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": "b12345"}],
                )
            ],
        )
        assert [i.format_field() for i in bib.get_fields("945")] == ["b12345"]
        assert len(bib.get_fields("945")) > len(original_945s)

    def test_update_fields_target_field_to_delete(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="*b2=a;")],
            )
        )
        original_949s = bib.get_fields("949")
        updater = marc_handler.MarcUpdater()
        updater.update_fields(
            bib,
            field_updates=[
                models.MarcFieldUpdateValues(
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": "*b2=a;bn=zzzzz;"}],
                    target_field_to_delete=models.TargetFieldCriteria(
                        tag="949", indicators=(" ", " "), code="a", value="*b2=a;"
                    ),
                )
            ],
        )
        assert [i.format_field() for i in bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;bn=zzzzz;",
        ]
        assert "*b2=a;bn=zzzzz;" not in original_949s

    def test_update_fields_target_field_to_delete_not_found(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        updater = marc_handler.MarcUpdater()
        updater.update_fields(
            bib,
            field_updates=[
                models.MarcFieldUpdateValues(
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": "*b2=a;bn=zzzzz;"}],
                    target_field_to_delete=models.TargetFieldCriteria(
                        tag="949", indicators=(" ", " "), code="a", value="*"
                    ),
                )
            ],
        )
        assert [i.format_field() for i in bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;bn=zzzzz;",
        ]

    def test_update_leader_encoding(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        updater = marc_handler.MarcUpdater()
        updater.update_leader_encoding(bib=bib, leader="00000cam  2200517 i 4500")
        assert bib.leader == "00000cam a2200517 i 4500"
