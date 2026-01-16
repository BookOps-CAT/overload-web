import copy

import pytest
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain_services import parse
from overload_web.bib_records.infrastructure import marc_mapper


@pytest.fixture
def full_parser_service(library, test_constants):
    return parse.FullLevelBibParser(
        mapper=marc_mapper.BookopsMarcMapper(
            rules=test_constants["mapper_rules"], library=library, record_type="cat"
        )
    )


@pytest.fixture
def order_parser_service(library, test_constants):
    return parse.OrderLevelBibParser(
        mapper=marc_mapper.BookopsMarcMapper(
            rules=test_constants["mapper_rules"], library=library, record_type="acq"
        )
    )


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestParser:
    def test_parse_full(self, full_parser_service, full_bib, caplog):
        records = full_parser_service.parse(full_bib.binary_data)
        assert len(records) == 1
        assert records[0].library == full_parser_service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info.name == "UNKNOWN"
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.parametrize(
        "tag, value", [("901", "BTSERIES"), ("947", "B&amp;T SERIES")]
    )
    def test_parse_full_vendor(self, full_parser_service, stub_bib, tag, value, caplog):
        stub_vendor_bib = copy.deepcopy(stub_bib)
        stub_vendor_bib.add_field(
            Field(
                tag=tag,
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=value)],
            )
        )
        records = full_parser_service.parse(stub_vendor_bib.as_marc())
        assert len(records) == 1
        assert records[0].library == full_parser_service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is not None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_order_level(
        self, order_parser_service, order_level_bib, collection, caplog
    ):
        records = order_parser_service.parse(order_level_bib.binary_data)
        assert len(records) == 1
        assert records[0].library == order_parser_service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].collection == collection
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_no_005(self, order_parser_service, stub_bib, caplog):
        stub_bib.remove_fields("005")
        records = order_parser_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].vendor_info is None
        assert records[0].update_date is None
        assert records[0].update_datetime is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg
