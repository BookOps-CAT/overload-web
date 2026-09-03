import datetime

import pytest
from pymarc import Field, Indicators, Subfield

from overload_web.application.pvf import marc


class TestParser:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_parse_full(self, parser_engine, stub_bib, collection, record_type, caplog):
        records = marc.BibParser.parse_marc_data(
            parser=parser_engine, data=stub_bib.as_marc()
        )
        assert len(records) == 1
        assert records[0].library == parser_engine.library
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
        self, parser_engine, stub_bib, tag, value, caplog
    ):
        stub_bib.add_field(
            Field(
                tag=tag,
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        records = marc.BibParser.parse_marc_data(
            parser=parser_engine, data=stub_bib.as_marc()
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
        self, parser_engine, stub_bib, collection, record_type, caplog
    ):
        records = marc.BibParser.parse_marc_data(
            parser=parser_engine, data=stub_bib.as_marc()
        )
        assert len(records) == 1
        assert records[0].library == parser_engine.library
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
    def test_parse_update_datetime(self, parser_engine, stub_bib):
        stub_bib.add_field(Field(tag="005", data="20200101010000.0"))
        records = marc.BibParser.parse_marc_data(
            parser=parser_engine, data=stub_bib.as_marc()
        )
        assert len(records) == 1
        assert records[0].update_date == "20200101010000.0"
        assert records[0].update_datetime == datetime.datetime(2020, 1, 1, 1, 0, 0, 0)
