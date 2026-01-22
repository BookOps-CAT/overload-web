import copy

import pandas as pd
import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain_models import bibs
from overload_web.bib_records.domain_services import analysis, update


@pytest.fixture
def bib_with_command_tag(order_level_bib):
    def create_match_result(value):
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
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        )
        full_bib.vendor = "BT SERIES"
        return full_bib

    return make_full_bib


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
        full_bib.bib_id = "12345"
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        updated_bibs = updater_service.update(record=full_bib)
        updated_bib = Bib(updated_bibs.binary_data, library=updated_bibs.library)
        assert len(original_bib.get_fields(tag)) == 0
        assert len(updated_bib.get_fields(tag)) == 1

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat")],
    )
    def test_update_cat_nypl_vendor_fields(self, full_bib, updater_service):
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
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        updated_bibs = updater_service.update(record=full_bib)
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(
                Bib(updated_bibs.binary_data, library=updated_bibs.library).get_fields(
                    "949"
                )
            )
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("bpl", "NONE", "cat")],
    )
    def test_update_cat_bpl_vendor_fields(self, full_bib, updater_service):
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
        original_bib = Bib(full_bib.binary_data, library=full_bib.library)
        updated_bibs = updater_service.update(record=full_bib)
        assert len(original_bib.get_fields("949")) == 0
        assert (
            len(
                Bib(updated_bibs.binary_data, library=updated_bibs.library).get_fields(
                    "949"
                )
            )
            == 1
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_update_template_data(self, order_level_bib, updater_service):
        original_orders = copy.deepcopy(order_level_bib.orders)
        updated_bibs = updater_service.update(
            order_level_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs.orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel")],
    )
    @pytest.mark.parametrize("value", ["*b2=a;", "*b2=a;bn=;", "*b2=a"])
    def test_update_default_loc(self, bib_with_command_tag, updater_service, value):
        result = bib_with_command_tag(value)
        original_bib = Bib(result.binary_data, library=result.library)
        updated_records = updater_service.update(result, template_data={})
        updated_bib = Bib(updated_records.binary_data, library=updated_records.library)
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
    def test_update_default_loc_bpl(self, bib_with_command_tag, updater_service, value):
        result = bib_with_command_tag(value)
        original_bib = Bib(result.binary_data, library=result.library)
        updated_records = updater_service.update(result, template_data={})
        updated_bib = Bib(updated_records.binary_data, library=updated_records.library)
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
        self, updater_service, bib_with_command_tag
    ):
        result = bib_with_command_tag("*b2=a;")
        original_bib = Bib(result.binary_data, library=result.library)
        updated_records = updater_service.update(result, template_data={"format": "a"})
        updated_bib = Bib(updated_records.binary_data, library=updated_records.library)
        assert len(updated_bib.get_fields("949")) == 2
        assert len(original_bib.get_fields("949")) == 2

    @pytest.mark.parametrize(
        "library, collection, field_count",
        [("nypl", "BL", 2), ("nypl", "RL", 2), ("bpl", "NONE", 1)],
    )
    @pytest.mark.parametrize("record_type", ["sel"])
    def test_update_no_command_tag_bpl(
        self, order_level_bib, updater_service, field_count
    ):
        original_bib = Bib(order_level_bib.binary_data, library=order_level_bib.library)
        updated_records = updater_service.update(order_level_bib, template_data={})
        updated_bib = Bib(updated_records.binary_data, library=updated_records.library)
        assert len(updated_bib.get_fields("949")) == field_count
        assert len(original_bib.get_fields("949")) == 1

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
        self, make_bt_series_full_bib, updater_service, pairs
    ):
        result = make_bt_series_full_bib(pairs)
        original_bib = Bib(result.binary_data, library=result.library)
        updated_records = updater_service.update(result)
        updated_bib = Bib(updated_records.binary_data, library=updated_records.library)
        assert updated_bib.get_fields("091")[0].value() == " ".join(
            [i for i in pairs.values()]
        )
        assert original_bib.get_fields("091")[0].value() == " ".join(
            [i for i in pairs.values()]
        )
        assert original_bib.collection == "BL"
        assert result.vendor == "BT SERIES"
        assert result.record_type == "cat"

    @pytest.mark.parametrize(
        "library, collection, record_type", [("nypl", "BL", "cat")]
    )
    def test_update_bt_series_call_no_error(
        self, make_bt_series_full_bib, updater_service
    ):
        result = make_bt_series_full_bib(
            {"z": "FOO", "p": "J", "a": "FIC", "c": "SNICKET"}
        )
        with pytest.raises(ValueError) as exc:
            updater_service.update(result)
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FOO J FIC SNICKET, Original=FIC SNICKET"
        )


class TestMatchAnalysisReport:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_report(self, full_bib, sierra_response, library, collection, record_type):
        rep = analysis.NYPLCatBranchMatchAnalyzer()
        result = rep.analyze_match(record=full_bib, candidates=[sierra_response])
        report = bibs.MatchAnalysisReport(
            analyses=[result],
            library=library,
            collection=collection,
            record_type=record_type,
        )
        report_dict = report.to_dict()
        assert sorted(list(report_dict.keys())) == sorted(
            [
                "resource_id",
                "vendor",
                "updated_by_vendor",
                "call_number_match",
                "target_call_no",
                "call_number",
                "duplicate_records",
                "target_bib_id",
                "target_title",
                "mixed",
                "other",
                "action",
                "library",
                "collection",
                "record_type",
                "corrected",
                "date",
            ]
        )
        assert len(report_dict["action"]) == 1
        assert len(report_dict["call_number"]) == 1
        assert len(report_dict["call_number_match"]) == 1
        assert len(report_dict["duplicate_records"]) == 1
        assert len(report_dict["mixed"]) == 1
        assert len(report_dict["other"]) == 1
        assert len(report_dict["resource_id"]) == 1
        assert len(report_dict["target_bib_id"]) == 1
        assert len(report_dict["target_call_no"]) == 1
        assert len(report_dict["target_title"]) == 1
        assert len(report_dict["updated_by_vendor"]) == 1
        assert len(report_dict["vendor"]) == 1
        assert len(report_dict["library"]) == 1
        assert len(report_dict["collection"]) == 1
        assert len(report_dict["record_type"]) == 1
        assert len(report_dict["corrected"]) == 1
        df = pd.DataFrame(data=report_dict)
        assert list(df.columns) == [
            "resource_id",
            "vendor",
            "updated_by_vendor",
            "call_number_match",
            "target_call_no",
            "call_number",
            "duplicate_records",
            "target_bib_id",
            "target_title",
            "mixed",
            "other",
            "action",
            "library",
            "collection",
            "record_type",
            "corrected",
            "date",
        ]
        assert df.shape == (1, 17)
