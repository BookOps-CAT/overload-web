import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain_services import update


@pytest.fixture
def bib_with_command_tag(order_level_bib):
    def order_bib(value):
        bib = copy.deepcopy(order_level_bib)
        record = Bib(order_level_bib.binary_data, library=order_level_bib.library)
        record.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        bib.binary_data = record.as_marc()
        return bib

    return order_bib


class TestUpdater:
    @pytest.fixture
    def updater_service(self, update_strategy):
        return update.BibUpdater(strategy=update_strategy)

    @pytest.mark.parametrize(
        "library, collection, tag, record_type",
        [
            ("bpl", "NONE", "907", "cat"),
            ("nypl", "BL", "945", "cat"),
            ("nypl", "RL", "945", "cat"),
        ],
    )
    def test_update_cat(self, full_bib, updater_service, tag):
        original_bib = Bib(
            copy.deepcopy(full_bib.binary_data), library=full_bib.library
        )
        full_bib.bib_id = "12345"
        updated_bibs = updater_service.update([full_bib])
        updated_bib = Bib(updated_bibs[0].binary_data, library=updated_bibs[0].library)
        assert len(original_bib.get_fields(tag)) == 0
        assert len(updated_bib.get_fields(tag)) == 1

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_update_cat_vendor_fields(self, full_bib, library, updater_service):
        full_bib.vendor = "INGRAM"
        full_bib.vendor_info = update.bibs.VendorInfo(
            name="INGRAM",
            matchpoints={"primary_matchpoint": "oclc_number"},
            bib_fields=[
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        )
        original_bib = copy.deepcopy(Bib(full_bib.binary_data, library=library))
        updated_bibs = updater_service.update([full_bib])
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_update_template_data(
        self, order_level_bib, fake_template_data, updater_service, record_type
    ):
        order_level_bib.record_type = record_type
        original_orders = copy.deepcopy(order_level_bib.orders)
        updated_bibs = updater_service.update(
            [order_level_bib], template_data=fake_template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel")],
    )
    @pytest.mark.parametrize("value", ["*b2=a;", "*b2=a;bn=;", "*b2=a"])
    def test_update_default_loc(
        self, bib_with_command_tag, updater_service, library, collection, value
    ):
        bib = bib_with_command_tag(value)
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        updated_records = updater_service.update([bib], template_data={})
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890",
            value,
        ]
        assert updated_bib.get_fields("949")[0].value() == "333331234567890"
        assert updated_bib.get_fields("949")[1].value().startswith("*b2=a;bn=") is True

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("bpl", "NONE", "sel")],
    )
    @pytest.mark.parametrize("value", ["*b2=a;", "*b2=a;bn=;", "*b2=a"])
    def test_update_default_loc_bpl(
        self, bib_with_command_tag, updater_service, library, collection, value
    ):
        bib = bib_with_command_tag(value)
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        updated_records = updater_service.update([bib], template_data={})
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert [i.value() for i in original_bib.get_fields("949")] == [
            "333331234567890",
            value,
        ]
        assert [i.value() for i in updated_bib.get_fields("949")] == [
            "333331234567890",
            value,
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_update_default_loc_no_command_tag(
        self, updater_service, bib_with_command_tag, library, collection
    ):
        bib = bib_with_command_tag("*b2=a;")
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        updated_records = updater_service.update([bib], template_data={"format": "a"})
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert len(updated_bib.get_fields("949")) == 2
        assert len(original_bib.get_fields("949")) == 2

    @pytest.mark.parametrize(
        "library, collection, record_type, field_count",
        [("nypl", "BL", "sel", 2), ("nypl", "RL", "sel", 2), ("bpl", "NONE", "sel", 1)],
    )
    def test_update_no_command_tag_bpl(
        self, order_level_bib, updater_service, record_type, library, field_count
    ):
        order_level_bib.record_type = record_type
        original_bib = copy.deepcopy(Bib(order_level_bib.binary_data, library=library))
        updated_records = updater_service.update([order_level_bib], template_data={})
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert len(updated_bib.get_fields("949")) == field_count
        assert len(original_bib.get_fields("949")) == 1

    @pytest.mark.parametrize("library, record_type", [("nypl", "cat")])
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
        ],
    )
    def test_update_bt_series_call_no(
        self, make_bt_series_full_bib, library, updater_service, pairs
    ):
        bib = make_bt_series_full_bib(pairs)
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        updated_records = updater_service.update([bib])
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert updated_bib.get_fields("091")[0].value() == " ".join(
            [i for i in pairs.values()]
        )
        assert original_bib.get_fields("091")[0].value() == " ".join(
            [i for i in pairs.values()]
        )
        assert original_bib.collection == "BL"
        assert bib.vendor == "BT SERIES"
        assert bib.record_type == "cat"

    @pytest.mark.parametrize("library, record_type", [("nypl", "cat")])
    def test_update_bt_series_call_no_error(
        self, make_bt_series_full_bib, library, updater_service
    ):
        bib = make_bt_series_full_bib(
            {"z": "FOO", "p": "J", "a": "FIC", "c": "SNICKET"}
        )
        with pytest.raises(ValueError) as exc:
            updater_service.update([bib])
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FOO J FIC SNICKET, Original=FIC SNICKET"
        )
