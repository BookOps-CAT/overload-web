import pytest

from overload_web.bib_records.domain_services import parse
from overload_web.bib_records.infrastructure import marc_mapper


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class Testparse:
    def test_parse_full(self, stub_constants, library, stub_bib, caplog):
        stub_service = parse.FullLevelBibParser(
            marc_mapper.BookopsMarcMapper(
                rules=stub_constants["mapper_rules"], library=library, record_type="cat"
            )
        )
        records, barcodes = stub_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert barcodes == ["333331234567890"]
        assert records[0].vendor_info is not None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_order_level(
        self, stub_constants, library, stub_bib, collection, caplog
    ):
        stub_service = stub_service = parse.OrderLevelBibParser(
            marc_mapper.BookopsMarcMapper(
                rules=stub_constants["mapper_rules"], library=library, record_type="acq"
            )
        )
        records = stub_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert str(records[0].collection) == str(collection)
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_no_005(self, stub_constants, library, stub_bib, collection, caplog):
        stub_bib.remove_fields("005")
        stub_service = stub_service = parse.OrderLevelBibParser(
            marc_mapper.BookopsMarcMapper(
                rules=stub_constants["mapper_rules"], library=library, record_type="sel"
            )
        )
        records = stub_service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].vendor_info is None
        assert records[0].update_date is None
        assert records[0].update_datetime is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg
