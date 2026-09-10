import pytest
from pymarc import Field, Indicators, Subfield

from overload_web.application.pvf import marc
from overload_web.infrastructure import marc_handler


@pytest.fixture
def parsing_handler(
    library, record_type, collection, get_constants
) -> marc_handler.MarcParsingHandler:
    rules = get_constants["parsing_rules"]
    return marc_handler.MarcParsingHandler(
        order_mapping=rules["order_mapping"],
        library=library,
        record_type=record_type,
        collection=collection,
        bib_mapping=rules["bib_mapping"],
        vendor_mapping=rules["vendor_rules"],
    )


class TestParser:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_parse_full(
        self, parsing_handler, stub_marc, collection, record_type, caplog
    ):
        records = marc.BibParser.parse_marc_data(
            parser=parsing_handler, data=stub_marc.as_marc()
        )
        assert len(records) == 1
        assert records[0].library == parsing_handler.library
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
        self, parsing_handler, stub_marc, tag, value, caplog
    ):
        stub_marc.add_field(
            Field(
                tag=tag,
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        records = marc.BibParser.parse_marc_data(
            parser=parsing_handler, data=stub_marc.as_marc()
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
        self, parsing_handler, stub_marc, collection, record_type, caplog
    ):
        records = marc.BibParser.parse_marc_data(
            parser=parsing_handler, data=stub_marc.as_marc()
        )
        assert len(records) == 1
        assert records[0].library == parsing_handler.library
        assert records[0].collection == collection
        assert records[0].record_type == record_type
        assert records[0].vendor_info is None
        assert records[0].vendor == "UNKNOWN"
        assert records[0].update_date is None
        assert records[0].update_datetime is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg
