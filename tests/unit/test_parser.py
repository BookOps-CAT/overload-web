import datetime

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.application.services import marc_services


@pytest.fixture
def stub_bib(library, collection) -> Bib:
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
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
    else:
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
            subfields=[
                Subfield(code="i", value="333331234567890"),
            ],
        )
    )
    bib.add_field(
        Field(
            tag="960",
            indicators=Indicators(" ", " "),
            subfields=[
                Subfield(code="c", value="j"),
                Subfield(code="d", value="c"),
                Subfield(code="e", value="d"),
                Subfield(code="f", value="a"),
                Subfield(code="g", value="b"),
                Subfield(code="i", value="l"),
                Subfield(code="m", value="o"),
                Subfield(code="o", value="13"),
                Subfield(code="q", value="01-01-25"),
                Subfield(code="s", value="{{dollar}}13.20"),
                Subfield(code="t", value="agj0y"),
                Subfield(code="u", value="lease"),
                Subfield(code="v", value="btlea"),
                Subfield(code="w", value="eng"),
                Subfield(code="x", value="xxu"),
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


class TestParser:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_parse_full(self, marc_engine, stub_bib, collection, record_type, caplog):
        records = marc_services.BibParser.parse_marc_data(
            stub_bib.as_marc(), engine=marc_engine
        )
        assert len(records) == 1
        assert records[0].library == marc_engine.library
        assert records[0].collection == collection
        assert records[0].record_type == record_type
        assert records[0].vendor_info.name == "UNKNOWN"
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.parametrize(
        "library, collection, record_type, tag, value",
        [
            ("nypl", "BL", "cat", "901", "BTSERIES"),
            ("nypl", "RL", "cat", "901", "BTSERIES"),
            ("bpl", "NONE", "cat", "947", "B&amp;T SERIES"),
        ],
    )
    def test_parse_full_with_vendor_data(
        self, marc_engine, stub_bib, tag, value, caplog
    ):
        stub_bib.add_field(
            Field(
                tag=tag,
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        records = marc_services.BibParser.parse_marc_data(
            stub_bib.as_marc(), engine=marc_engine
        )
        assert len(records) == 1
        assert records[0].vendor_info is not None
        assert records[0].vendor_info.name == "BT SERIES"

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "acq"),
            ("nypl", "BL", "sel"),
            ("nypl", "RL", "acq"),
            ("nypl", "RL", "sel"),
            ("bpl", "NONE", "acq"),
            ("bpl", "NONE", "sel"),
        ],
    )
    def test_parse_order_level(
        self, marc_engine, stub_bib, collection, record_type, caplog
    ):
        records = marc_services.BibParser.parse_marc_data(
            stub_bib.as_marc(), engine=marc_engine
        )
        assert len(records) == 1
        assert records[0].library == marc_engine.library
        assert records[0].collection == collection
        assert records[0].record_type == record_type
        assert records[0].vendor_info is None
        assert records[0].vendor == "UNKNOWN"
        assert records[0].update_date is None
        assert records[0].update_datetime is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [
            ("nypl", "BL", "acq"),
            ("nypl", "BL", "sel"),
            ("nypl", "RL", "acq"),
            ("nypl", "RL", "sel"),
            ("bpl", "NONE", "acq"),
            ("bpl", "NONE", "sel"),
        ],
    )
    def test_parse_update_datetime(self, marc_engine, stub_bib):
        stub_bib.add_field(Field(tag="005", data="20200101010000.0"))
        records = marc_services.BibParser.parse_marc_data(
            stub_bib.as_marc(), engine=marc_engine
        )
        assert len(records) == 1
        assert records[0].update_date == "20200101010000.0"
        assert records[0].update_datetime == datetime.datetime(2020, 1, 1, 1, 0, 0, 0)
