import pytest

from overload_web.bib_records.domain_services import parse
from overload_web.bib_records.infrastructure import marc_mapper


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
@pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
class TestParser:
    @pytest.fixture
    def fake_mapper(self, record_type, library, test_constants):
        return marc_mapper.BookopsMarcMapper(
            rules=test_constants["mapper_rules"],
            library=library,
            record_type=record_type,
        )

    def test_parse_full(self, fake_mapper, stub_bib, caplog):
        service = parse.FullLevelBibParser(mapper=fake_mapper)
        records = service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].library == service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is not None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_full_unknown_vendor(
        self, fake_mapper, stub_bib_unknown_vendor, caplog
    ):
        service = parse.FullLevelBibParser(mapper=fake_mapper)
        records = service.parse(stub_bib_unknown_vendor.as_marc())
        assert len(records) == 1
        assert records[0].library == service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is not None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_full_alt_vendor_tags(self, fake_mapper, stub_bib_alt_vendor, caplog):
        service = parse.FullLevelBibParser(mapper=fake_mapper)
        records = service.parse(stub_bib_alt_vendor.as_marc())
        assert len(records) == 1
        assert records[0].library == service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is not None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_order_level(self, fake_mapper, stub_bib, collection, caplog):
        service = parse.OrderLevelBibParser(mapper=fake_mapper)
        records = service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].library == service.mapper.library
        assert records[0].isbn == "9781234567890"
        assert records[0].collection == collection
        assert records[0].barcodes == ["333331234567890"]
        assert records[0].vendor_info is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_parse_no_005(self, fake_mapper, stub_bib, caplog):
        stub_bib.remove_fields("005")
        service = parse.OrderLevelBibParser(mapper=fake_mapper)
        records = service.parse(stub_bib.as_marc())
        assert len(records) == 1
        assert records[0].vendor_info is None
        assert records[0].update_date is None
        assert records[0].update_datetime is None
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg
