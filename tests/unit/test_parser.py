import pytest

from overload_web.bib_records.domain import bib_services
from overload_web.bib_records.infrastructure import marc_mapper


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestParser:
    def test_parse_full(self, stub_constants, library, stub_full_bib, caplog):
        stub_service = bib_services.BibParser(
            marc_mapper.BookopsMarcFullBibMapper(
                rules=stub_constants["mapper_rules"], library=library, record_type="cat"
            )
        )
        records = stub_service.parse(stub_full_bib.binary_data)
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert records[0].barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_order_level(
        self, stub_constants, library, stub_order_bib, collection, caplog
    ):
        stub_service = stub_service = bib_services.BibParser(
            marc_mapper.BookopsMarcOrderBibMapper(
                rules=stub_constants["mapper_rules"], library=library, record_type="sel"
            )
        )
        records = stub_service.parse(stub_order_bib.binary_data)
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert str(records[0].collection) == str(collection)
        assert records[0].barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestRecordProcessingSerializer:
    def test_serialize(self, stub_order_bib, caplog):
        stub_service = bib_services.BibSerializer()
        marc_binary = stub_service.serialize(records=[stub_order_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
