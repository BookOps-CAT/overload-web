import copy

import pytest

from overload_web.application import services
from overload_web.domain import protocols


class MockRepository(protocols.repositories.SqlRepositoryProtocol):
    def __init__(self, templates):
        self.templates = templates


class StubFetcher(protocols.bibs.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def get_bibs_by_id(self, value, key):
        bib_1 = {"bib_id": "123", "isbn": "9781234567890"}
        bib_2 = {"bib_id": "234", "isbn": "1234567890", "oclc_number": "123456789"}
        bib_3 = {"bib_id": "345", "isbn": "9781234567890", "oclc_number": "123456789"}
        bib_4 = {"bib_id": "456", "upc": "333"}
        return [bib_1, bib_2, bib_3, bib_4]


@pytest.mark.parametrize(
    "library, collection, record_type",
    [
        ("nypl", "BL", "full"),
        ("nypl", "BL", "order_level"),
        ("nypl", "RL", "full"),
        ("nypl", "RL", "order_level"),
        ("bpl", "NONE", "full"),
        ("bpl", "NONE", "order_level"),
    ],
)
class TestRecordProcessingService:
    stub_mapping = {
        "907": {"a": "bib_id"},
        "960": {
            "c": "order_code_1",
            "d": "order_code_2",
            "e": "order_code_3",
            "f": "order_code_4",
            "g": "format",
            "i": "order_type",
            "m": "status",
            "o": "copies",
            "q": "create_date",
            "s": "price",
            "t": "locations",
            "u": "fund",
            "v": "vendor_code",
            "w": "lang",
            "x": "country",
            "z": "order_id",
        },
        "961": {
            "d": "internal_note",
            "f": "selector_note",
            "h": "vendor_notes",
            "i": "vendor_title_no",
            "m": "blanket_po",
        },
    }

    @pytest.fixture
    def stub_service(self, monkeypatch, library, collection, record_type):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher()

        monkeypatch.setattr(
            "overload_web.infrastructure.bibs.sierra.SierraBibFetcher", fake_fetcher
        )
        return services.records.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            marc_rules=self.stub_mapping,
        )

    @pytest.fixture
    def stub_service_no_matches(self, monkeypatch, library, collection, record_type):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.infrastructure.bibs.sierra.SierraBibFetcher", fake_fetcher
        )
        return services.records.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            marc_rules=self.stub_mapping,
        )

    @pytest.fixture
    def stub_bib_dto(self, library, make_bib_dto):
        dto = make_bib_dto({"020": {"code": "a", "value": "9781234567890"}})
        return dto

    def test_parse(self, stub_service, stub_bib_dto):
        records = stub_service.parse(stub_bib_dto.bib.as_marc())
        assert len(records) == 1
        assert str(records[0].bib.library) == str(stub_service.library)
        assert records[0].bib.isbn == "9781234567890"
        assert str(records[0].domain_bib.library) == str(stub_service.library)
        assert records[0].domain_bib.barcodes == ["333331234567890"]

    def test_process_records(self, stub_service, stub_bib_dto, template_data):
        original_orders = copy.deepcopy(stub_bib_dto.domain_bib.orders)
        matched_bibs = stub_service.process_records([stub_bib_dto], template_data)
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].domain_bib.orders] == ["b"]

    def test_process_records_no_matches(self, stub_service_no_matches, stub_bib_dto):
        matched_bibs = stub_service_no_matches.process_records(
            [stub_bib_dto], template_data={}
        )
        assert len(matched_bibs) == 1
        assert matched_bibs[0].domain_bib.bib_id is None

    def test_process_records_vendor_updates(self, stub_service, make_bib_dto):
        dto = make_bib_dto(
            {
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(dto.bib)
        matched_bibs = stub_service.process_records([dto], template_data={})
        assert len(matched_bibs) == 1
        assert len(original_bib.get_fields("949")) == 1
        assert len(matched_bibs[0].bib.get_fields("949")) == 2

    def test_write_marc_binary(self, stub_bib_dto, stub_service):
        marc_binary = stub_service.write_marc_binary(records=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"
