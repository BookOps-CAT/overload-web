import datetime

import pytest

from overload_web.infrastructure import bibs


@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestBookopsMarcMapper:
    def test_map_order(self, stub_bib):
        mapper = bibs.marc.BookopsMarcMapper()
        mapped_order = mapper.map_order(stub_bib.orders[0])
        assert mapped_order.create_date == datetime.date(2025, 1, 1)
        assert mapped_order.lang == "eng"
        assert mapped_order.blanket_po == "baz"

    def test_map_order_no_961(self, stub_bib):
        stub_bib.remove_fields("961")
        mapper = bibs.marc.BookopsMarcMapper()
        mapped_order = mapper.map_order(stub_bib.orders[0])
        assert mapped_order.create_date == datetime.date(2025, 1, 1)
        assert mapped_order.lang == "eng"
        assert mapped_order.blanket_po is None

    def test_map_bib(self, stub_bib):
        mapper = bibs.marc.BookopsMarcMapper()
        mapped_bib = mapper.map_bib(stub_bib)
        assert mapped_bib.bib_id is None
        assert mapped_bib.barcodes == ["333331234567890"]
        assert mapped_bib.oclc_number == []
        assert len(mapped_bib.orders) == 1
        assert mapped_bib.orders[0].create_date == datetime.date(2025, 1, 1)
        assert mapped_bib.orders[0].lang == "eng"
        assert mapped_bib.orders[0].blanket_po == "baz"
