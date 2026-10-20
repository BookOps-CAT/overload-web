import copy

import pytest

from overload_web.domain.pvf import models, services
from overload_web.infrastructure import marc_handler


@pytest.fixture
def stub_domain_bib(request):
    marker = request.node.get_closest_marker("workflow")
    barcode = "333331234567890"
    bib = models.DomainBib(
        library=marker.kwargs["library"],
        collection=marker.kwargs["collection"],
        title="Foo",
        record_type=marker.kwargs["record_type"],
        binary_data=b"",
        barcodes=[barcode],
        orders=[],
        vendor_info=models.VendorInfo(name="UNKNOWN", bib_fields=[], matchpoints={}),
        parsed_fields=[],
    )
    bib.parsed_fields = [
        models.ParsedField(
            tag="949",
            indicators=(" ", "1"),
            subfields=[models.ParsedSubfield(code="i", value=barcode)],
        )
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


@pytest.fixture
def stub_updater(get_constants):
    constants = get_constants["constants"]

    return services.BibUpdater(
        handler=marc_handler.MarcUpdater(),
        default_locations=constants["default_locations"],
        bib_id_tags=constants["bib_id_tag"],
        order_mapping=constants["order_mapping"],
    )


class TestBibUpdater:
    @pytest.mark.workflow(library="bpl", collection=None, record_type="acq")
    def test_get_order_level_updates_acq_bpl(self, stub_updater, stub_domain_bib):
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=stub_domain_bib,
            library="bpl",
            collection=None,
            record_type="acq",
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in stub_domain_bib.orders] == ["b"]
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    @pytest.mark.workflow(library="bpl", collection=None, record_type="sel")
    def test_get_order_level_updates_sel_bpl(self, stub_updater, stub_domain_bib):
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        updates = stub_updater.get_order_level_updates(
            library="bpl",
            collection=None,
            record_type="sel",
            record=stub_domain_bib,
            template_data={"order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in stub_domain_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": "*b2=a;"}]
        assert updates[2].target_field_to_delete is None

    @pytest.mark.workflow(library="bpl", collection=None, record_type="sel")
    def test_get_order_level_updates_sel_bpl_with_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="*b2=a;")],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            library="bpl",
            collection=None,
            record_type="sel",
            record=stub_domain_bib,
            template_data={"format": "a"},
        )
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    @pytest.mark.workflow(library="bpl", collection=None, record_type="sel")
    def test_get_order_level_updates_sel_bpl_no_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        updates = stub_updater.get_order_level_updates(
            library="bpl",
            collection=None,
            record_type="sel",
            record=stub_domain_bib,
            template_data={},
        )
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    @pytest.mark.workflow(library="bpl", collection=None, record_type="cat")
    def test_get_full_record_updates_bpl(self, stub_updater, stub_domain_bib):
        stub_domain_bib.bib_id = "12345"
        stub_domain_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_full_record_updates(
            library="bpl", collection=None, record=stub_domain_bib
        )
        assert len(updates) == 2
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_fields_by_tag": False,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "907",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="acq")
    def test_get_order_level_updates_acq_nypl_bl(self, stub_updater, stub_domain_bib):
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=stub_domain_bib,
            library="nypl",
            collection="BL",
            record_type="acq",
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in stub_domain_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].__dict__ == {
            "tag": "910",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "BL"}],
        }

    @pytest.mark.parametrize(
        "template, command_tag",
        [
            ({"order_code_1": "b", "format": "a"}, "*b2=a;bn=zzzzz;"),
            ({"order_code_1": "b"}, "*bn=zzzzz;"),
        ],
    )
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="sel")
    def test_get_order_level_updates_sel_nypl_bl(
        self, stub_updater, stub_domain_bib, template, command_tag
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="b2=a")],
            )
        ]
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="BL",
            record_type="sel",
            record=stub_domain_bib,
            template_data=template,
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in stub_domain_bib.orders] == ["b"]
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": command_tag}]
        assert updates[2].target_field_to_delete is None
        assert updates[3].tag == "910"

    @pytest.mark.parametrize(
        "original, output",
        [("*b2=a;", "*b2=a;bn=zzzzz;"), ("*b2=a", "*b2=a;bn=zzzzz;")],
    )
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="sel")
    def test_get_order_level_updates_sel_nypl_bl_check_command_tag(
        self, stub_updater, stub_domain_bib, original, output
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value=original)],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="BL",
            record_type="sel",
            record=stub_domain_bib,
            template_data={"order_code_1": "b", "format": "a"},
        )
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": output}]
        assert updates[2].target_field_to_delete.__dict__ == {
            "tag": "949",
            "indicators": (" ", " "),
            "code": "a",
            "value": original,
        }
        assert updates[3].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="sel")
    def test_get_order_level_updates_sel_nypl_bl_skip_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="*b2=a;bn=zzzzz;")],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="BL",
            record_type="sel",
            record=stub_domain_bib,
            template_data={"order_code_1": "b", "format": "a"},
        )
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_get_full_record_updates_nypl_bl(self, stub_updater, stub_domain_bib):
        stub_domain_bib.bib_id = "12345"
        stub_domain_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_full_record_updates(
            library="nypl", collection="BL", record=stub_domain_bib
        )
        assert len(updates) == 3
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_fields_by_tag": False,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "945",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
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
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_get_full_record_updates_nypl_bl_bt_series_call_no(
        self, stub_updater, stub_domain_bib, input, output
    ):
        stub_domain_bib.vendor = "BT SERIES"
        stub_domain_bib.branch_call_number = " ".join([i for i in input.values()])
        updates = stub_updater.get_full_record_updates(
            library="nypl", collection="BL", record=stub_domain_bib
        )
        assert len(updates) == 2
        assert updates[0].tag == "910"
        assert updates[1].tag == "091"
        assert updates[1].ind1 == " "
        assert updates[1].ind2 == " "
        assert updates[1].delete_fields_by_tag is True
        assert updates[1].target_field_to_delete is None
        assert updates[1].subfields == [
            {"code": k, "value": v} for k, v in output.items()
        ]

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_get_full_record_updates_nypl_bl_bt_series_call_no_error(
        self, stub_domain_bib, stub_updater
    ):

        stub_domain_bib.vendor = "BT SERIES"
        stub_domain_bib.branch_call_number = "FOO J FIC SNICKET"
        with pytest.raises(ValueError) as exc:
            stub_updater.get_full_record_updates(
                library="nypl", collection="BL", record=stub_domain_bib
            )
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FIC SNICKET, Original=FOO J FIC SNICKET"
        )

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="acq")
    def test_get_order_level_updates_acq_nypl_rl(self, stub_updater, stub_domain_bib):
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="RL",
            record_type="acq",
            record=stub_domain_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in stub_domain_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].__dict__ == {
            "tag": "910",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "RL"}],
        }

    @pytest.mark.parametrize(
        "template, command_tag",
        [
            ({"order_code_1": "b", "format": "a"}, "*b2=a;bn=xxx;"),
            ({"order_code_1": "b"}, "*bn=xxx;"),
        ],
    )
    @pytest.mark.workflow(library="nypl", collection="RL", record_type="sel")
    def test_get_order_level_updates_sel_nypl_rl(
        self, stub_updater, stub_domain_bib, template, command_tag
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="b2=a")],
            )
        ]
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="RL",
            record_type="sel",
            record=stub_domain_bib,
            template_data=template,
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in stub_domain_bib.orders] == ["b"]
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": command_tag}]
        assert updates[2].target_field_to_delete is None
        assert updates[3].tag == "910"

    @pytest.mark.parametrize(
        "original, output", [("*b2=a;", "*b2=a;bn=xxx;"), ("*b2=a", "*b2=a;bn=xxx;")]
    )
    @pytest.mark.workflow(library="nypl", collection="RL", record_type="sel")
    def test_get_order_level_updates_sel_nypl_rl_check_command_tag(
        self, stub_updater, stub_domain_bib, original, output
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value=original)],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="RL",
            record_type="sel",
            record=stub_domain_bib,
            template_data={"order_code_1": "b", "format": "a"},
        )
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": output}]
        assert updates[2].target_field_to_delete.__dict__ == {
            "tag": "949",
            "indicators": (" ", " "),
            "code": "a",
            "value": original,
        }

        assert updates[3].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="sel")
    def test_get_order_level_updates_sel_nypl_rl_skip_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        stub_domain_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="*b2=a;bn=xxx;")],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            library="nypl",
            collection="RL",
            record_type="sel",
            record=stub_domain_bib,
            template_data={"order_code_1": "b", "format": "a"},
        )
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="cat")
    def test_get_full_record_updates_nypl_rl(self, stub_updater, stub_domain_bib):
        stub_domain_bib.bib_id = "12345"
        stub_domain_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_full_record_updates(
            library="nypl", collection="RL", record=stub_domain_bib
        )
        assert len(updates) == 3
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_fields_by_tag": False,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "945",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }
        assert updates[2].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_apply_field_updates(self, stub_updater, stub_domain_bib):
        updates = stub_updater.get_full_record_updates(
            library="nypl", collection="BL", record=stub_domain_bib
        )
        stub_updater.apply_field_updates(record=stub_domain_bib, updates=updates)

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="acq")
    def test_write(self, stub_updater, stub_domain_bib):
        out = stub_updater.write(records=[stub_domain_bib])
        assert isinstance(out, bytes)
