import copy
import datetime

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain_services import parse
from overload_web.bib_records.infrastructure import marc_mapper


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


@pytest.fixture
def full_parser_service(library, get_constants):
    rules = get_constants["mapper_rules"]
    return parse.BibParser(
        mapper=marc_mapper.FullRecordMarcMapper(
            rules=rules, library=library, record_type="cat"
        )
    )


@pytest.fixture
def order_parser_service(library, get_constants):
    rules = get_constants["mapper_rules"]
    return parse.BibParser(
        mapper=marc_mapper.OrderLevelMarcMapper(
            rules=rules, library=library, record_type="acq"
        )
    )


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestParser:
    def test_parse_full(self, full_parser_service, stub_bib, caplog):
        records = full_parser_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].library == full_parser_service.mapper.library
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
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is not None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_order_level(
        self, order_parser_service, stub_bib, collection, caplog
    ):
        records = order_parser_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].library == order_parser_service.mapper.library
        assert records[0].collection == collection
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is None
        assert records[0].update_date is None
        assert records[0].update_datetime is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_update_date(self, order_parser_service, stub_bib, caplog):
        stub_bib.add_field(Field(tag="005", data="20200101010000.0"))
        records = order_parser_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].vendor_info is None
        assert records[0].update_date == "20200101010000.0"
        assert records[0].update_datetime == datetime.datetime(2020, 1, 1, 1, 0, 0, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_extract_barcodes(self, order_parser_service, stub_bib):
        records = order_parser_service.parse(stub_bib.as_marc())
        barcodes = order_parser_service.extract_barcodes(records)
        assert len(barcodes) == 1
