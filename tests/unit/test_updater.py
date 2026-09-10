import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.application.pvf import update
from overload_web.domain.pvf import marc_rules, models
from overload_web.domain.shared import fields
from overload_web.infrastructure import marc_handler


@pytest.fixture
def bib_with_command_tag(sel_bib):
    def create_match_result(value):
        bib = copy.deepcopy(sel_bib)
        record = Bib(sel_bib.binary_data, library=sel_bib.library)
        record.add_ordered_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        bib.binary_data = record.as_marc()
        bib.parsed_fields.append(
            fields.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[fields.ParsedSubfield(code="a", value=value)],
            )
        )
        return bib

    return create_match_result


@pytest.fixture
def make_bt_series_full_bib(full_bib, library, collection):
    def make_full_bib(pairs):
        bib = Bib(full_bib.binary_data, library=full_bib.library)
        bib.remove_fields("091")
        subfield_list = []
        for k, v in pairs.items():
            subfield_list.append(Subfield(code=k, value=v))
        call_no = Field(
            tag="091", indicators=Indicators(" ", " "), subfields=subfield_list
        )
        bib.add_field(call_no)
        bib.add_field(
            Field(
                tag="901",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="BTSERIES")],
            )
        )
        full_bib.branch_call_number = call_no.value()
        full_bib.binary_data = bib.as_marc()
        full_bib.vendor_info = models.VendorInfo(
            name="BT SERIES",
            matchpoints={
                "primary_matchpoint": "isbn",
                "secondary_matchpoint": "control_number",
            },
            bib_fields=[
                {"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}
            ],
        )
        full_bib.vendor = "BT SERIES"
        return full_bib

    return make_full_bib


@pytest.fixture
def stub_full_bib(full_bib):
    new_full_bib = copy.deepcopy(full_bib)
    new_full_bib.control_number = "123456789"
    return new_full_bib


@pytest.fixture
def full_bib_add_barcodes(stub_full_bib, library):
    new_full_bib = copy.deepcopy(stub_full_bib)
    new_bib = Bib(new_full_bib.binary_data, library=library)
    if library == "bpl":
        new_bib.remove_fields("960")
        new_bib.add_field(
            Field(
                tag="960",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="333331111111111")],
            )
        )
    else:
        new_bib.remove_fields("949")
        new_bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", "1"),
                subfields=[Subfield(code="i", value="333331111111111")],
            )
        )
        new_bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="i", value="*b2=a;")],
            )
        )
    parsed_fields = []
    for field in new_bib.fields:
        if field.subfields:
            parsed_fields.append(
                fields.ParsedField(
                    tag=field.tag,
                    indicators=(field.indicator1, field.indicator2),
                    subfields=[
                        fields.ParsedSubfield(code=sf.code, value=sf.value)
                        for sf in field.subfields
                    ],
                )
            )
        else:
            parsed_fields.append(fields.ParsedField(tag=field.tag, value=field.data))
    new_full_bib.binary_data = new_bib.as_marc()
    new_full_bib.parsed_fields = parsed_fields
    new_full_bib.barcodes = ["333331111111111"]
    return new_full_bib


@pytest.fixture
def stub_updater(library, record_type, collection, get_constants):
    constants = get_constants["constants"]
    return update.BibUpdater(
        order_mapping=constants["order_mapping"],
        default_loc=constants["default_locations"][library].get(collection),
        bib_id_tag=constants["bib_id_tag"][library],
        library=library,
        record_type=record_type,
        collection=collection,
    )


@pytest.fixture
def update_rules(library, record_type, collection, get_constants):
    constants = get_constants["constants"]
    return {
        "order_mapping": constants["order_mapping"],
        "default_loc": constants["default_locations"][library].get(collection),
        "bib_id_tag": constants["bib_id_tag"][library],
        "library": library,
        "record_type": record_type,
        "collection": collection,
    }


class TestUpdaterAcqRecords:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_update_with_template_data(self, acq_bib, update_rules):
        """Updates orders based on template data."""
        original_orders = copy.deepcopy(acq_bib.orders)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_acq_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        updater.update_record(record=acq_bib, handler=self.ENGINE, updates=updates)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_update_check_command_tag(self, update_rules, bib_with_command_tag):
        """Checks for existing command tag based on format. Updates with default location."""
        input_bib = bib_with_command_tag("*b2=a;")
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_acq_updates(
            record=input_bib, template_data={"format": "a"}
        )
        updater.update_record(record=input_bib, handler=self.ENGINE, updates=updates)
        updated_bib = Bib(input_bib.binary_data, library=input_bib.library)
        assert len(updated_bib.get_fields("949")) == 2
        assert len(original_bib.get_fields("949")) == 2
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;",
        ]
        assert [i.value() for i in updated_bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;",
        ]


class TestUpdaterCatRecords:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection, tag, record_type",
        [
            ("bpl", "NONE", "907", "cat"),
            ("nypl", "BL", "945", "cat"),
            ("nypl", "RL", "945", "cat"),
        ],
    )
    def test_update(self, full_bib, update_rules, tag):
        """Adds bib_id to appropriate tag"""
        full_bib.bib_id = "12345"
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_cat_updates(record=full_bib)
        updater.update_record(record=full_bib, handler=self.ENGINE, updates=updates)
        updated_bib = Bib(full_bib.binary_data, library=full_bib.library)
        assert len(original_bib.get_fields(tag)) == 0
        assert len(updated_bib.get_fields(tag)) == 1

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat")],
    )
    def test_update_vendor_fields_nypl(self, full_bib, update_rules):
        """Adds command tag based on vendor info. Results in two 949 fields."""
        full_bib.vendor = "INGRAM"
        full_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={"primary_matchpoint": "control_number"},
            bib_fields=[
                {"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}
            ],
        )
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_cat_updates(record=full_bib)
        updater.update_record(record=full_bib, handler=self.ENGINE, updates=updates)
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(full_bib.binary_data, library=full_bib.library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection, record_type", [("bpl", "NONE", "cat")]
    )
    def test_update_vendor_fields_bpl(self, full_bib, update_rules):
        """Adds command tag based on vendor info. Results in one 949 field."""
        full_bib.vendor = "INGRAM"
        full_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={"primary_matchpoint": "control_number"},
            bib_fields=[
                {"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}
            ],
        )
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_cat_updates(record=full_bib)
        updater.update_record(record=full_bib, handler=self.ENGINE, updates=updates)
        assert len(original_bib.get_fields("949")) == 0
        assert (
            len(Bib(full_bib.binary_data, library=full_bib.library).get_fields("949"))
            == 1
        )

    @pytest.mark.parametrize(
        "library, collection, record_type", [("nypl", "BL", "cat")]
    )
    @pytest.mark.parametrize(
        "pairs",
        [
            {"p": "J", "a": "FIC", "c": "SNICKET"},
            {"p": "J", "f": "HOLIDAY", "a": "PIC", "c": "MONTES"},
            {"p": "J", "f": "YR", "a": "FIC", "c": "WEST"},
            {"p": "J SPA", "a": "PIC", "c": "J"},
            {"f": "GRAPHIC", "a": "FIC", "c": "OCONNOR"},
            {"p": "J E COMPOUND NAME"},
            {"p": "J SPA E COMPOUND NAME"},
            {"p": "J", "f": "GRAPHIC", "a": "GN FIC", "c": "SMITH"},
            {"f": "DVD", "a": "MOVIE", "c": "MISSISSIPPI"},
        ],
    )
    def test_update_bt_series_call_no(
        self, make_bt_series_full_bib, update_rules, pairs
    ):
        input_bib = make_bt_series_full_bib(pairs)
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_cat_updates(record=input_bib)
        updater.update_record(record=input_bib, handler=self.ENGINE, updates=updates)
        updated_bib = Bib(input_bib.binary_data, library=input_bib.library)
        assert updated_bib.get_fields("091")[0].value() == " ".join(
            [i for i in pairs.values()]
        )
        assert original_bib.get_fields("091")[0].value() == " ".join(
            [i for i in pairs.values()]
        )
        assert original_bib.collection == "BL"
        assert input_bib.vendor == "BT SERIES"
        assert input_bib.record_type == "cat"

    @pytest.mark.parametrize(
        "library, collection, record_type", [("nypl", "BL", "cat")]
    )
    def test_update_bt_series_call_no_error(
        self, make_bt_series_full_bib, update_rules
    ):
        input_bib = make_bt_series_full_bib(
            {"z": "FOO", "p": "J", "a": "FIC", "c": "SNICKET"}
        )
        with pytest.raises(ValueError) as exc:
            updater = update.BibUpdater(**update_rules)
            updates = updater.get_cat_updates(record=input_bib)
            updater.update_record(
                record=input_bib, handler=self.ENGINE, updates=updates
            )
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FIC SNICKET, Original=FOO J FIC SNICKET"
        )


class TestUpdaterSelRecords:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_update_template_data(self, sel_bib, update_rules):
        """Updates orders based on template data."""
        original_orders = copy.deepcopy(sel_bib.orders)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_sel_updates(
            sel_bib, template_data={"name": "Foo", "order_code_1": "b", "format": "a"}
        )
        updater.update_record(sel_bib, handler=self.ENGINE, updates=updates)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection, record_type, original, output",
        [
            ("nypl", "BL", "sel", "*b2=a;", "*b2=a;bn=zzzzz;"),
            ("nypl", "BL", "sel", "*b2=a;bn=;", "*b2=a;bn=;"),
            ("nypl", "BL", "sel", "*b2=a", "*b2=a;bn=zzzzz;"),
            ("nypl", "RL", "sel", "*b2=a;", "*b2=a;bn=xxx;"),
            ("nypl", "RL", "sel", "*b2=a;bn=;", "*b2=a;bn=;"),
            ("nypl", "RL", "sel", "*b2=a", "*b2=a;bn=xxx;"),
            ("bpl", "NONE", "sel", "*b2=a;", "*b2=a;"),
            ("bpl", "NONE", "sel", "*b2=a;bn=;", "*b2=a;bn=;"),
            ("bpl", "NONE", "sel", "*b2=a", "*b2=a"),
        ],
    )
    def test_update_default_loc(
        self, bib_with_command_tag, update_rules, original, output
    ):
        """Updates existing command tag with default location."""
        input_bib = bib_with_command_tag(original)
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_sel_updates(input_bib, template_data={})
        updater.update_record(input_bib, handler=self.ENGINE, updates=updates)
        updated_bib = Bib(input_bib.binary_data, library=input_bib.library)
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890",
            original,
        ]
        assert [i.value() for i in updated_bib.get_fields("949")] == [
            "333331234567890",
            output,
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type, output",
        [
            ("nypl", "BL", "sel", "*b2=a;bn=zzzzz;"),
            ("nypl", "RL", "sel", "*b2=a;bn=xxx;"),
            ("bpl", "NONE", "sel", "*b2=a;"),
        ],
    )
    def test_update_check_command_tag(self, update_rules, bib_with_command_tag, output):
        """Checks for existing command tag based on format. Updates with default location."""
        input_bib = bib_with_command_tag("*b2=a;")
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_sel_updates(input_bib, template_data={"format": "a"})
        updater.update_record(input_bib, handler=self.ENGINE, updates=updates)
        updated_bib = Bib(input_bib.binary_data, library=input_bib.library)
        assert len(updated_bib.get_fields("949")) == 2
        assert len(original_bib.get_fields("949")) == 2
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890",
            "*b2=a;",
        ]
        assert [i.value() for i in updated_bib.get_fields("949")] == [
            "333331234567890",
            output,
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type, field_count, output",
        [
            ("nypl", "BL", "sel", 2, ["333331234567890", "*bn=zzzzz;"]),
            ("nypl", "RL", "sel", 2, ["333331234567890", "*bn=xxx;"]),
            ("bpl", "NONE", "sel", 1, ["333331234567890"]),
        ],
    )
    def test_update_no_command_tag_bpl(
        self, sel_bib, update_rules, field_count, output
    ):
        """Adds command tag with default location."""
        original_bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        updater = update.BibUpdater(**update_rules)
        updates = updater.get_sel_updates(sel_bib, template_data={})
        updater.update_record(sel_bib, handler=self.ENGINE, updates=updates)
        updated_bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        assert len(updated_bib.get_fields("949")) == field_count
        assert len(original_bib.get_fields("949")) == 1
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890"
        ]
        assert [i.value() for i in updated_bib.get_fields("949")] == output

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_command_tag_not_found(self, sel_bib):
        """Tests `_find_specific_field` method."""
        bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        criteria = marc_rules.TargetFieldCriteria(
            tag="500",
            indicators=(" ", " "),
            subfield_code="a",
            subfield_starts_with="Foo",
        )
        field = self.ENGINE._find_specific_field(bib, criteria=criteria)
        assert field is None


@pytest.mark.parametrize("record_type", ["cat"])
class TestDeduplicate:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_attach(self, stub_full_bib, stub_updater):
        bib = copy.deepcopy(stub_full_bib)
        bib.action = models.CatalogAction.ATTACH
        processed = stub_updater.deduplicate(records=[bib], handler=self.ENGINE)
        assert len(processed["NEW"]) == 0
        assert len(processed["DUP"]) == 1
        assert len(processed["DEDUPED"]) == 0

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_insert(self, stub_full_bib, stub_updater):
        bib = copy.deepcopy(stub_full_bib)
        bib.action = models.CatalogAction.INSERT
        processed = stub_updater.deduplicate(records=[bib], handler=self.ENGINE)
        assert len(processed["NEW"]) == 1
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 0

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_dedupe_combine_bpl_bibs(
        self, library, stub_full_bib, full_bib_add_barcodes, stub_updater
    ):
        bib = copy.deepcopy(stub_full_bib)
        bib_add_barcodes = copy.deepcopy(full_bib_add_barcodes)
        bib.action = models.CatalogAction.INSERT
        bib_add_barcodes.action = models.CatalogAction.INSERT
        processed = stub_updater.deduplicate(
            records=[bib, bib_add_barcodes], handler=self.ENGINE
        )
        deduped = Bib(processed["DEDUPED"][0].binary_data, library=library)
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 1
        assert sorted([i.value() for i in deduped.get_fields("960")]) == [
            "333331111111111",
            "333331234567890",
        ]
        assert [i.control_number for i in processed["NEW"]] == [
            "123456789",
            "123456789",
        ]
        assert [i.control_number for i in processed["DEDUPED"]] == ["123456789"]

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_dedupe_bpl_overdrive_bibs(
        self, library, stub_bib, full_bib_add_barcodes, stub_updater
    ):
        bib = copy.deepcopy(stub_bib)
        bib_add_barcodes = copy.deepcopy(full_bib_add_barcodes)
        bib.action = models.CatalogAction.INSERT
        bib_add_barcodes.action = models.CatalogAction.INSERT
        processed = stub_updater.deduplicate(
            records=[bib, bib_add_barcodes], handler=self.ENGINE
        )
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 0

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_dedupe_combine_nypl_bibs(
        self, library, stub_full_bib, full_bib_add_barcodes, stub_updater
    ):
        bib = copy.deepcopy(stub_full_bib)
        bib_add_barcodes = copy.deepcopy(full_bib_add_barcodes)
        bib.action = models.CatalogAction.INSERT
        bib_add_barcodes.action = models.CatalogAction.INSERT
        processed = stub_updater.deduplicate(
            records=[bib, bib_add_barcodes], handler=self.ENGINE
        )
        deduped = Bib(processed["DEDUPED"][0].binary_data, library=library)
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 1
        assert sorted([i.value() for i in deduped.get_fields("949")]) == [
            "333331111111111",
            "333331234567890",
        ]
        assert [i.control_number for i in processed["NEW"]] == [
            "123456789",
            "123456789",
        ]
        assert [i.control_number for i in processed["DEDUPED"]] == ["123456789"]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_other_recs(
        self, stub_full_bib, full_bib_add_barcodes, stub_updater
    ):
        bib = copy.deepcopy(stub_full_bib)
        bib_add_barcodes = copy.deepcopy(full_bib_add_barcodes)
        other_rec = copy.deepcopy(stub_full_bib)
        other_rec.control_number = "987654321"
        other_rec.action = models.CatalogAction.INSERT
        bib.action = models.CatalogAction.INSERT
        bib_add_barcodes.action = models.CatalogAction.INSERT
        processed = stub_updater.deduplicate(
            records=[bib, bib_add_barcodes, other_rec], handler=self.ENGINE
        )
        assert len(processed["NEW"]) == 3
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 2
        assert sorted([i.control_number for i in processed["NEW"]]) == [
            "123456789",
            "123456789",
            "987654321",
        ]
        assert sorted([i.control_number for i in processed["DEDUPED"]]) == [
            "123456789",
            "987654321",
        ]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_multiple_groups(
        self, stub_full_bib, full_bib_add_barcodes, stub_updater
    ):
        bib_1a = copy.deepcopy(stub_full_bib)
        bib_1a.action = models.CatalogAction.INSERT
        bib_1b = copy.deepcopy(full_bib_add_barcodes)
        bib_1b.action = models.CatalogAction.INSERT
        bib2 = copy.deepcopy(stub_full_bib)
        bib2.control_number = None
        bib2.action = models.CatalogAction.INSERT
        bib3 = copy.deepcopy(stub_full_bib)
        bib3.control_number = None
        bib3.action = models.CatalogAction.INSERT
        bib4 = copy.deepcopy(stub_full_bib)
        bib4.control_number = "987654321"
        bib4.action = models.CatalogAction.INSERT
        processed = stub_updater.deduplicate(
            records=[bib_1a, bib_1b, bib2, bib3, bib4], handler=self.ENGINE
        )
        assert len(processed["NEW"]) == 5
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 4
        assert [i.control_number for i in processed["NEW"]] == [
            "123456789",
            "123456789",
            None,
            None,
            "987654321",
        ]
        assert [i.control_number for i in processed["DEDUPED"]] == [
            "123456789",
            None,
            None,
            "987654321",
        ]
