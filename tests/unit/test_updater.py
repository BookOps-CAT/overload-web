import copy
import random

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.application.pvf import update_service
from overload_web.domain import shared
from overload_web.domain.pvf import marc_rules, models
from overload_web.infrastructure import marc_handler


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
                shared.ParsedField(
                    tag=field["tag"],
                    indicators=(field["ind1"], field["ind2"]),
                    subfields=[
                        shared.ParsedSubfield(code=i["code"], value=i["value"])
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
def stub_updater(request, get_constants):
    marker = request.node.get_closest_marker("workflow")
    collection = marker.kwargs["collection"]
    library = marker.kwargs["library"]
    constants = get_constants["constants"]
    return update_service.BibUpdater(
        order_mapping=constants["order_mapping"],
        default_loc=constants["default_locations"][library].get(collection),
        bib_id_tag=constants["bib_id_tag"][library],
        library=library,
        collection=collection,
        handler=marc_handler.MarcUpdater(),
    )


@pytest.fixture
def stub_reviewer():
    return update_service.BibReviewer(handler=marc_handler.MarcUpdater())


@pytest.fixture
def stub_domain_bib(request, stub_bib):
    marker = request.node.get_closest_marker("workflow")

    def make_bib(record_type):
        bib = stub_bib(
            marker.kwargs["library"], marker.kwargs["collection"], record_type
        )
        bib.parsed_fields = [
            shared.ParsedField(tag="005", value="20200101010000.0"),
            shared.ParsedField(
                tag="020",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="i", value="9781234567890")],
            ),
            shared.ParsedField(
                tag="949",
                indicators=(" ", "1"),
                subfields=[shared.ParsedSubfield(code="i", value="333331234567890")],
            ),
        ]
        bib.orders = [
            models.Order(
                locations=["agj0y"],
                audience=["j"],
                branches=["ag"],
                copies="13",
                create_date="01-01-25",
                format="b",
                lang="eng",
                order_id=".o10000010",
                shelves=["0y"],
                status="o",
                vendor_notes=None,
                order_code_1="j",
                order_code_2="c",
                order_code_3="d",
                order_code_4="a",
                order_type="l",
                price="{{dollar}}13.20",
                project_code="A01",
                fund="lease",
                vendor_code="btlea",
                country="xxu",
                internal_note="foo",
                selector_note="bar",
                vendor_title_no=None,
                blanket_po="baz",
            )
        ]
        return bib

    return make_bib


@pytest.mark.workflow(library="bpl", collection=None)
class TestGetBibUpdatesBPL:
    def test_get_acq_updates(self, stub_updater, stub_domain_bib):
        acq_bib = stub_domain_bib("acq")
        original_orders = copy.deepcopy(acq_bib.orders)
        updates = stub_updater.get_acq_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    def test_get_cat_updates(self, stub_updater, stub_domain_bib):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_cat_updates(record=cat_bib)
        assert len(updates) == 2
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_all_by_tag": False,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "907",
            "delete_all_by_tag": True,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }

    def test_get_sel_updates(self, stub_updater, stub_domain_bib):
        sel_bib = stub_domain_bib("sel")
        original_orders = copy.deepcopy(sel_bib.orders)
        updates = stub_updater.get_sel_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": "*b2=a;"}]
        assert updates[2].target_to_delete is None

    def test_get_sel_updates_with_command_tag(self, stub_updater, stub_domain_bib):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value="*b2=a;")],
            )
        ]
        updates = stub_updater.get_sel_updates(
            record=sel_bib, template_data={"format": "a"}
        )
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    def test_get_sel_updates_no_command_tag(self, stub_updater, stub_domain_bib):
        sel_bib = stub_domain_bib("sel")
        updates = stub_updater.get_sel_updates(record=sel_bib, template_data={})
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"


@pytest.mark.workflow(library="nypl", collection="BL")
class TestGetBibUpdatesNYPLBranch:
    def test_get_acq_updates(self, stub_updater, stub_domain_bib):
        acq_bib = stub_domain_bib("acq")
        original_orders = copy.deepcopy(acq_bib.orders)
        updates = stub_updater.get_acq_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].__dict__ == {
            "tag": "910",
            "delete_all_by_tag": True,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "BL"}],
        }

    def test_get_cat_updates(self, stub_updater, stub_domain_bib):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_cat_updates(record=cat_bib)
        assert len(updates) == 3
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_all_by_tag": False,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "945",
            "delete_all_by_tag": True,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }
        assert updates[2].tag == "910"

    @pytest.mark.parametrize(
        "input,output",
        [
            ({"p": "J", "a": "FIC", "c": "FOO"}, {"p": "J", "a": "FIC", "c": "FOO"}),
            (
                {"p": "J", "f": "HOLIDAY", "a": "PIC", "c": "BAR"},
                {"p": "J", "f": "HOLIDAY", "a": "PIC", "c": "BAR"},
            ),
            (
                {"p": "J", "f": "YR", "a": "FIC", "c": "BAZ"},
                {"p": "J", "f": "YR", "a": "FIC", "c": "BAZ"},
            ),
            (
                {"p": "J SPA", "a": "PIC", "c": "J"},
                {"p": "J SPA", "a": "PIC", "c": "J"},
            ),
            (
                {"f": "GRAPHIC", "a": "FIC", "c": "FOO"},
                {"f": "GRAPHIC", "a": "FIC", "c": "FOO"},
            ),
            ({"p": "J E FOO BAR"}, {"p": "J", "a": "E", "c": "FOO BAR"}),
            ({"p": "J SPA E FOO BAR"}, {"p": "J SPA", "a": "E", "c": "FOO BAR"}),
            (
                {"p": "J", "f": "GRAPHIC", "a": "GN FIC", "c": "BAZ"},
                {"p": "J", "f": "GRAPHIC", "a": "GN FIC", "c": "BAZ"},
            ),
            ({"f": "DVD", "a": "MOVIE", "c": "BAZ"}, {"c": "DVD MOVIE BAZ"}),
        ],
    )
    def test_get_cat_updates_bt_series_call_no(
        self, stub_updater, stub_domain_bib, input, output
    ):
        cat_bib = stub_domain_bib("cat")
        cat_bib.vendor = "BT SERIES"
        cat_bib.branch_call_number = " ".join([i for i in input.values()])
        updates = stub_updater.get_cat_updates(record=cat_bib)
        assert len(updates) == 2
        assert updates[0].tag == "910"
        assert updates[1].tag == "091"
        assert updates[1].ind1 == " "
        assert updates[1].ind2 == " "
        assert updates[1].delete_all_by_tag is True
        assert updates[1].target_to_delete is None
        assert updates[1].subfields == [
            {"code": k, "value": v} for k, v in output.items()
        ]

    def test_get_cat_updates_bt_series_call_no_error(
        self, stub_domain_bib, stub_updater
    ):
        cat_bib = stub_domain_bib("cat")
        cat_bib.vendor = "BT SERIES"
        cat_bib.branch_call_number = "FOO J FIC SNICKET"
        with pytest.raises(ValueError) as exc:
            stub_updater.get_cat_updates(record=cat_bib)
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FIC SNICKET, Original=FOO J FIC SNICKET"
        )

    @pytest.mark.parametrize(
        "template, command_tag",
        [
            ({"order_code_1": "b", "format": "a"}, "*b2=a;bn=zzzzz;"),
            ({"order_code_1": "b"}, "*bn=zzzzz;"),
        ],
    )
    def test_get_sel_updates(
        self, stub_updater, stub_domain_bib, template, command_tag
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value="b2=a")],
            )
        ]
        original_orders = copy.deepcopy(sel_bib.orders)
        updates = stub_updater.get_sel_updates(record=sel_bib, template_data=template)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": command_tag}]
        assert updates[2].target_to_delete is None
        assert updates[3].tag == "910"

    @pytest.mark.parametrize(
        "original, output",
        [("*b2=a;", "*b2=a;bn=zzzzz;"), ("*b2=a", "*b2=a;bn=zzzzz;")],
    )
    def test_get_sel_updates_check_command_tag(
        self, stub_updater, stub_domain_bib, original, output
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value=original)],
            )
        ]
        updates = stub_updater.get_sel_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": output}]
        assert updates[2].target_to_delete.__dict__ == {
            "tag": "949",
            "indicators": (" ", " "),
            "code": "a",
            "value": original,
        }
        assert updates[3].tag == "910"

    def test_get_sel_updates_skip_command_tag(self, stub_updater, stub_domain_bib):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value="*b2=a;bn=zzzzz;")],
            )
        ]
        updates = stub_updater.get_sel_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "910"


@pytest.mark.workflow(library="nypl", collection="RL")
class TestGetBibUpdatesNYPLResearch:
    def test_get_acq_updates(self, stub_updater, stub_domain_bib):
        acq_bib = stub_domain_bib("acq")
        original_orders = copy.deepcopy(acq_bib.orders)
        updates = stub_updater.get_acq_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].__dict__ == {
            "tag": "910",
            "delete_all_by_tag": True,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "RL"}],
        }

    def test_get_cat_updates(self, stub_updater, stub_domain_bib):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_cat_updates(record=cat_bib)
        assert len(updates) == 3
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_all_by_tag": False,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "945",
            "delete_all_by_tag": True,
            "target_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }
        assert updates[2].tag == "910"

    @pytest.mark.parametrize(
        "template, command_tag",
        [
            ({"order_code_1": "b", "format": "a"}, "*b2=a;bn=xxx;"),
            ({"order_code_1": "b"}, "*bn=xxx;"),
        ],
    )
    def test_get_sel_updates(
        self, stub_updater, stub_domain_bib, template, command_tag
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value="b2=a")],
            )
        ]
        original_orders = copy.deepcopy(sel_bib.orders)
        updates = stub_updater.get_sel_updates(record=sel_bib, template_data=template)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": command_tag}]
        assert updates[2].target_to_delete is None
        assert updates[3].tag == "910"

    @pytest.mark.parametrize(
        "original, output", [("*b2=a;", "*b2=a;bn=xxx;"), ("*b2=a", "*b2=a;bn=xxx;")]
    )
    def test_get_sel_updates_check_command_tag(
        self, stub_updater, stub_domain_bib, original, output
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value=original)],
            )
        ]
        updates = stub_updater.get_sel_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": output}]
        assert updates[2].target_to_delete.__dict__ == {
            "tag": "949",
            "indicators": (" ", " "),
            "code": "a",
            "value": original,
        }

        assert updates[3].tag == "910"

    def test_get_sel_updates_skip_command_tag(self, stub_updater, stub_domain_bib):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value="*b2=a;bn=xxx;")],
            )
        ]
        updates = stub_updater.get_sel_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "910"


class TestMarcUpdater:
    ENGINE = marc_handler.MarcUpdater()

    @pytest.mark.workflow(library="bpl", collection=None)
    def test_update_record_add_vendor_fields(self, stub_domain_bib, stub_updater):
        cat_bib = stub_domain_bib("cat")
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        stub_updater.apply_field_updates(
            cat_bib,
            updates=marc_rules.FieldRules.add_vendor_fields(
                cat_bib.vendor_info.bib_fields
            ),
        )
        updated_bib = Bib(cat_bib.binary_data, library=cat_bib.library)
        assert [i.format_field() for i in updated_bib.get_fields("949")] == ["*b2=a;"]

    @pytest.mark.workflow(library="nypl", collection="RL")
    def test_update_record_add_bib_id(self, stub_domain_bib, stub_updater):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        stub_updater.apply_field_updates(
            cat_bib, updates=[marc_rules.FieldRules.add_bib_id(cat_bib.bib_id, "945")]
        )
        updated_bib = Bib(cat_bib.binary_data, library=cat_bib.library)
        assert updated_bib["945"].format_field() == "12345"

    @pytest.mark.workflow(library="nypl", collection="BL")
    def test_update_record_command_tag(self, stub_domain_bib, stub_updater):
        field_949 = "*b2=a;"
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            shared.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[shared.ParsedSubfield(code="a", value=field_949)],
            )
        ]
        marc_data = Bib()
        marc_data.leader = "00000cam  2200517 i 4500"
        marc_data.library = sel_bib.library
        marc_data.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", "1"),
                subfields=[Subfield(code="a", value="333339876543210")],
            )
        )
        marc_data.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=field_949)],
            )
        )
        sel_bib.binary_data = marc_data.as_marc()
        stub_updater.apply_field_updates(
            sel_bib,
            updates=[
                marc_rules.FieldRules.add_command_tag(
                    format="a", default_loc="zzzzz", fields=sel_bib.parsed_fields
                )
            ],
        )
        updated_bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        fields_949 = [i.format_field() for i in updated_bib.get_fields("949")]
        assert len(fields_949) == 2
        assert "333339876543210" in fields_949
        assert "*b2=a;bn=zzzzz;" in fields_949

    @pytest.mark.workflow(library="nypl", collection="BL")
    def test_update_record_original_command_tag_not_found(
        self, stub_domain_bib, stub_updater
    ):
        sel_bib = stub_domain_bib("sel")
        original = copy.deepcopy(sel_bib)
        stub_updater.apply_field_updates(
            sel_bib,
            updates=[
                marc_rules.MarcFieldUpdateValues(
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": "*b2=a;bn=zzzzz;"}],
                    target_to_delete=marc_rules.TargetFieldCriteria(
                        tag="949", indicators=(" ", " "), code="a", value="*"
                    ),
                )
            ],
        )
        updated_bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        original_bib = Bib(original.binary_data, library=original.library)
        assert [i.format_field() for i in original_bib.get_fields("949")] == []
        assert [i.format_field() for i in updated_bib.get_fields("949")] == [
            "*b2=a;bn=zzzzz;"
        ]
