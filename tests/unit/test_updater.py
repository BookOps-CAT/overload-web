import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.application.services import marc_services
from overload_web.domain.models import bibs


@pytest.fixture
def bib_with_command_tag(sel_bib):
    def create_match_result(value):
        bib = copy.deepcopy(sel_bib)
        record = Bib(sel_bib.binary_data, library=sel_bib.library)
        record.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        bib.binary_data = record.as_marc()
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
        bib.add_field(
            Field(tag="091", indicators=Indicators(" ", " "), subfields=subfield_list)
        )
        bib.add_field(
            Field(
                tag="901",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="BTSERIES")],
            )
        )
        full_bib.binary_data = bib.as_marc()
        full_bib.vendor_info = bibs.VendorInfo(
            name="BT SERIES",
            matchpoints={
                "primary_matchpoint": "isbn",
                "secondary_matchpoint": "oclc_number",
            },
            bib_fields=[
                {"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}
            ],
        )
        full_bib.vendor = "BT SERIES"
        return full_bib

    return make_full_bib


class TestUpdater:
    @pytest.mark.parametrize(
        "library, collection, tag, record_type",
        [
            ("bpl", "NONE", "907", "cat"),
            ("nypl", "BL", "945", "cat"),
            ("nypl", "RL", "945", "cat"),
        ],
    )
    def test_update_cat(self, full_bib, marc_engine, tag):
        """Adds bib_id to appropriate tag"""
        full_bib.bib_id = "12345"
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        marc_services.BibUpdater.update_record(record=full_bib, engine=marc_engine)
        updated_bib = Bib(full_bib.binary_data, library=full_bib.library)
        assert len(original_bib.get_fields(tag)) == 0
        assert len(updated_bib.get_fields(tag)) == 1

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat")],
    )
    def test_update_cat_vendor_fields_nypl(self, full_bib, marc_engine):
        """Adds command tag based on vendor info. Results in two 949 fields."""
        full_bib.vendor = "INGRAM"
        full_bib.vendor_info = bibs.VendorInfo(
            name="INGRAM",
            matchpoints={"primary_matchpoint": "oclc_number"},
            bib_fields=[
                {"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}
            ],
        )
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        marc_services.BibUpdater.update_record(record=full_bib, engine=marc_engine)
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(full_bib.binary_data, library=full_bib.library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("bpl", "NONE", "cat")],
    )
    def test_update_cat_vendor_fields_bpl(self, full_bib, marc_engine):
        """Adds command tag based on vendor info. Results in one 949 field."""
        full_bib.vendor = "INGRAM"
        full_bib.vendor_info = bibs.VendorInfo(
            name="INGRAM",
            matchpoints={"primary_matchpoint": "oclc_number"},
            bib_fields=[
                {"tag": "949", "ind1": "", "ind2": "", "code": "a", "value": "*b2=a;"}
            ],
        )
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        marc_services.BibUpdater.update_record(record=full_bib, engine=marc_engine)
        assert len(original_bib.get_fields("949")) == 0
        assert (
            len(Bib(full_bib.binary_data, library=full_bib.library).get_fields("949"))
            == 1
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_update_template_data_acq(self, acq_bib, marc_engine):
        """Updates orders based on template data."""
        original_orders = copy.deepcopy(acq_bib.orders)
        marc_services.BibUpdater.update_record(
            acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
            engine=marc_engine,
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_update_template_data_sel(self, sel_bib, marc_engine):
        """Updates orders based on template data."""
        original_orders = copy.deepcopy(sel_bib.orders)
        marc_services.BibUpdater.update_record(
            sel_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
            engine=marc_engine,
        )
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
        self, bib_with_command_tag, marc_engine, original, output
    ):
        """Updates existing command tag with default location."""
        input_bib = bib_with_command_tag(original)
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        marc_services.BibUpdater.update_record(
            input_bib, template_data={}, engine=marc_engine
        )
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
    def test_update_check_command_tag(self, marc_engine, bib_with_command_tag, output):
        """Checks for existing command tag based on format. Updates with default location."""
        input_bib = bib_with_command_tag("*b2=a;")
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        marc_services.BibUpdater.update_record(
            input_bib, template_data={"format": "a"}, engine=marc_engine
        )
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
    def test_update_no_command_tag_bpl(self, sel_bib, marc_engine, field_count, output):
        """Adds command tag with default location."""
        original_bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        marc_services.BibUpdater.update_record(
            sel_bib, template_data={}, engine=marc_engine
        )
        updated_bib = Bib(sel_bib.binary_data, library=sel_bib.library)
        assert len(updated_bib.get_fields("949")) == field_count
        assert len(original_bib.get_fields("949")) == 1
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890"
        ]
        assert [i.value() for i in updated_bib.get_fields("949")] == output

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
        self, make_bt_series_full_bib, marc_engine, pairs
    ):
        input_bib = make_bt_series_full_bib(pairs)
        original_bib = Bib(input_bib.binary_data, library=input_bib.library)
        marc_services.BibUpdater.update_record(input_bib, engine=marc_engine)
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
    def test_update_bt_series_call_no_error(self, make_bt_series_full_bib, marc_engine):
        input_bib = make_bt_series_full_bib(
            {"z": "FOO", "p": "J", "a": "FIC", "c": "SNICKET"}
        )
        with pytest.raises(ValueError) as exc:
            marc_services.BibUpdater.update_record(input_bib, engine=marc_engine)
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FIC SNICKET, Original=FOO J FIC SNICKET"
        )
