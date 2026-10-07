import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.pvf import models
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
    def test_identify_vendor_alternate_tags(
        self, stub_marc, get_constants, field, vendor
    ):
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

    def test_write(self, mock_marc):
        out = self.ENGINE.write([mock_marc.as_marc()])
        assert isinstance(out, bytes)


class TestMarcUpdater:
    ENGINE = marc_handler.MarcUpdater()

    def test_create_bib_from_domain(self, mock_marc):
        bib = self.ENGINE.create_bib_from_domain(
            library=mock_marc.library, binary_data=mock_marc.as_marc()
        )
        assert hasattr(bib, "control_number")

    @pytest.mark.workflow(library="nypl", collection="BL")
    def test_update_fields(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        original_949s = bib.get_fields("949")
        updates = models.FieldUpdates.add_vendor_fields(
            [{"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}]
        )
        self.ENGINE.update_fields(bib=bib, field_updates=updates)
        assert [i.format_field() for i in bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;",
        ]
        assert len(bib.get_fields("949")) > len(original_949s)

    @pytest.mark.workflow(library="nypl", collection="BL")
    def test_apply_field_updates_add_bib_id(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        original_945s = bib.get_fields("945")
        update = models.FieldUpdates.add_bib_id("b12345", "945")
        self.ENGINE.update_fields(bib=bib, field_updates=[update])
        assert [i.format_field() for i in bib.get_fields("945")] == ["b12345"]
        assert len(bib.get_fields("945")) > len(original_945s)

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_apply_field_updates_command_tag(self, stub_marc):
        field_949 = "*b2=a;"
        bib = copy.deepcopy(stub_marc)
        bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="*b2=a;")],
            )
        )
        original_949s = bib.get_fields("949")
        self.ENGINE.update_fields(
            bib,
            field_updates=[
                models.FieldUpdates.add_command_tag(
                    format="a",
                    default_loc="zzzzz",
                    fields=[
                        models.ParsedField(
                            tag="949",
                            indicators=(" ", " "),
                            subfields=[
                                models.ParsedSubfield(code="a", value=field_949)
                            ],
                        )
                    ],
                )
            ],
        )
        assert [i.format_field() for i in bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;bn=zzzzz;",
        ]
        assert "*b2=a;bn=zzzzz;" not in original_949s

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_apply_field_updates_original_command_tag_not_found(self, stub_marc):
        bib = copy.deepcopy(stub_marc)
        self.ENGINE.update_fields(
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

    def test_update_leader_encoding(self, mock_marc):
        bib = copy.deepcopy(mock_marc)
        self.ENGINE.update_leader_encoding(bib=bib, leader="00000cam  2200517 i 4500")
        assert bib.leader == "00000cam a2200517 i 4500"
