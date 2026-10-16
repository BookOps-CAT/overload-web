import datetime

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.pvf import services
from overload_web.infrastructure import marc_handler


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc(request) -> Bib:
    library = request.param[0]
    collection = request.param[1]
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
                tag="037",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="123"),
                    Subfield(code="b", value="OverDrive, Inc."),
                ],
            )
        )
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


class TestBibParser:
    ENGINE = marc_handler.MarcParser()

    def test_combine_marc_files(self, mock_marc, get_constants):
        rules = get_constants["parsing_rules"]
        rules["library"] = mock_marc.library
        rules["collection"] = mock_marc.collection
        rules["record_type"] = "cat"
        parser = services.BibParser(handler=marc_handler.MarcParser(), **rules)
        combined = parser.combine_marc_files(data=[mock_marc.as_marc()])
        assert len([i for i in combined]) > 1

    def test_parse_marc_data_order_level_record(self, mock_marc, get_constants, caplog):
        rules = get_constants["parsing_rules"]
        rules["library"] = mock_marc.library
        rules["collection"] = mock_marc.collection
        rules["record_type"] = "sel"
        parser = services.BibParser(handler=marc_handler.MarcParser(), **rules)
        records = parser.parse_marc_data(data=mock_marc.as_marc())
        assert len(records) == 1
        assert records[0].library == mock_marc.library
        assert records[0].record_type == "sel"
        assert records[0].vendor_info is None
        assert records[0].vendor == "UNKNOWN"
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.workflow(record_type="cat")
    def test_parse_marc_data_full_record(self, mock_marc, get_constants, caplog):
        rules = get_constants["parsing_rules"]
        rules["library"] = mock_marc.library
        rules["collection"] = mock_marc.collection
        rules["record_type"] = "cat"
        parser = services.BibParser(handler=marc_handler.MarcParser(), **rules)
        records = parser.parse_marc_data(data=mock_marc.as_marc())
        assert len(records) == 1
        assert records[0].library == mock_marc.library
        assert records[0].record_type == "cat"
        assert records[0].vendor_info.name == "UNKNOWN"
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg
