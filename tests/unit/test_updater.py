import copy

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain_services import update


class TestUpdater:
    @pytest.mark.parametrize(
        "library, collection, tag",
        [("bpl", "NONE", "907"), ("nypl", "BL", "945"), ("nypl", "RL", "945")],
    )
    @pytest.mark.parametrize("record_type", ["cat"])
    def test_update_cat(self, full_bib, update_strategy, tag):
        original_bib = Bib(
            copy.deepcopy(full_bib.binary_data), library=full_bib.library
        )

        full_bib.bib_id = "12345"
        service = update.BibUpdater(strategy=update_strategy)
        updated_bibs = service.update([full_bib])
        updated_bib = Bib(updated_bibs[0].binary_data, library=updated_bibs[0].library)
        assert len(original_bib.get_fields(tag)) == 0
        assert len(updated_bib.get_fields(tag)) == 1

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    @pytest.mark.parametrize("record_type", ["cat"])
    def test_update_cat_vendor_fields(self, full_bib, library, update_strategy):
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
        service = update.BibUpdater(strategy=update_strategy)
        updated_bibs = service.update([full_bib])
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    @pytest.mark.parametrize("record_type", ["acq", "sel"])
    def test_update_template_data(
        self, order_level_bib, fake_template_data, update_strategy, record_type
    ):
        order_level_bib.record_type = record_type
        original_orders = copy.deepcopy(order_level_bib.orders)
        service = update.BibUpdater(strategy=update_strategy)
        updated_bibs = service.update(
            [order_level_bib], template_data=fake_template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel")],
    )
    @pytest.mark.parametrize("value", ["*b2=a;", "*b2=a;bn=;", "*b2=a"])
    def test_update_default_loc(self, make_order_bib, update_strategy, library, value):
        bib = make_order_bib(value)
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        service = update.BibUpdater(strategy=update_strategy)
        updated_records = service.update([bib], template_data={})
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
        self, make_order_bib, update_strategy, library, value
    ):
        bib = make_order_bib(value)
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        service = update.BibUpdater(strategy=update_strategy)
        updated_records = service.update([bib], template_data={})
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
        self, update_strategy, make_order_bib, library
    ):
        bib = make_order_bib("*b2=a;")
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        service = update.BibUpdater(strategy=update_strategy)
        updated_records = service.update([bib], template_data={"format": "a"})
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert len(updated_bib.get_fields("949")) == 2
        assert len(original_bib.get_fields("949")) == 2

    @pytest.mark.parametrize(
        "library, collection, record_type, field_count",
        [("nypl", "BL", "sel", 2), ("nypl", "RL", "sel", 2), ("bpl", "NONE", "sel", 1)],
    )
    def test_update_no_command_tag_bpl(
        self, order_level_bib, update_strategy, record_type, library, field_count
    ):
        order_level_bib.record_type = record_type
        original_bib = copy.deepcopy(Bib(order_level_bib.binary_data, library=library))
        service = update.BibUpdater(strategy=update_strategy)
        updated_records = service.update([order_level_bib], template_data={})
        updated_bib = Bib(updated_records[0].binary_data, library=library)
        assert len(updated_bib.get_fields("949")) == field_count
        assert len(original_bib.get_fields("949")) == 1

    @pytest.mark.parametrize(
        "library, record_type",
        [("nypl", "cat")],
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
        ],
    )
    def test_update_bt_series_call_no(
        self, make_bt_series_full_bib, library, update_strategy, pairs
    ):
        bib = make_bt_series_full_bib(pairs)
        original_bib = copy.deepcopy(Bib(bib.binary_data, library=library))
        service = update.BibUpdater(strategy=update_strategy)
        updated_records = service.update([bib])
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

    @pytest.mark.parametrize(
        "library, record_type",
        [("nypl", "cat")],
    )
    def test_update_bt_series_call_no_error(
        self, make_bt_series_full_bib, library, update_strategy
    ):
        bib = make_bt_series_full_bib(
            {"z": "FOO", "p": "J", "a": "FIC", "c": "SNICKET"}
        )
        service = update.BibUpdater(strategy=update_strategy)
        with pytest.raises(ValueError) as exc:
            service.update([bib])
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FOO J FIC SNICKET, Original=FIC SNICKET"
        )
