import datetime

import pytest
from bookops_marc import Bib
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


@pytest.fixture
def stub_marc(library, collection) -> Bib:
    bib = Bib()
    bib.leader = "00000cam  2200517 i 4500"
    bib.library = library
    bib.add_field(Field(tag="005", data="20000101010001.0"))
    bib.add_field(
        Field(
            tag="020",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value="9781234567890")],
        )
    )
    if library == "bpl":
        bib.add_field(
            Field(
                tag="099",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="Foo")],
            )
        )
    else:
        if collection == "BL":
            bib.add_field(
                Field(
                    tag="091",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value="Foo")],
                )
            )
        else:
            bib.add_field(
                Field(
                    tag="852",
                    indicators=Indicators("8", " "),
                    subfields=[Subfield(code="a", value="Foo")],
                )
            )
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
            subfields=[Subfield(code="i", value="333331234567890")],
        )
    )
    bib.add_field(
        Field(
            tag="960",
            indicators=Indicators(" ", " "),
            subfields=[
                Subfield(code="a", value="l"),
                Subfield(code="b", value="-"),
                Subfield(code="c", value="j"),
                Subfield(code="d", value="c"),
                Subfield(code="e", value="d"),
                Subfield(code="f", value="a"),
                Subfield(code="g", value="b"),
                Subfield(code="h", value="-"),
                Subfield(code="i", value="l"),
                Subfield(code="j", value="-"),
                Subfield(code="k", value="A01"),
                Subfield(code="m", value="o"),
                Subfield(code="n", value="-"),
                Subfield(code="o", value="13"),
                Subfield(code="p", value="  -  -  "),
                Subfield(code="q", value="01-01-25"),
                Subfield(code="r", value="  -  -  "),
                Subfield(code="s", value="{{dollar}}13.20"),
                Subfield(code="t", value="agj0y"),
                Subfield(code="u", value="lease"),
                Subfield(code="v", value="btlea"),
                Subfield(code="w", value="eng"),
                Subfield(code="x", value="xxu"),
                Subfield(code="y", value="1"),
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
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_combine_marc_files(self, library, stub_marc):
        combined = marc.BibParser.combine_marc_files(
            marc_reader=marc_handler.MarcReaderWriter(library=library),
            data=[stub_marc.as_marc()],
        )
        assert len(combined) > 1

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
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg


class TestMarcReaderWriter:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_write(self, library, collection, stub_bib):
        bib = stub_bib(library, collection, "cat")
        writer = marc_handler.MarcReaderWriter(library=library)
        out = writer.write([bib])
        assert isinstance(out, bytes)
