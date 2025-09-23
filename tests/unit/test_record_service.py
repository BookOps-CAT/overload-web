import copy

import pytest

from overload_web.application import record_service
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
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestRecordProcessingService:
    @pytest.fixture
    def stub_service(
        self, monkeypatch, library, collection, record_type, stub_constants
    ):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher()

        monkeypatch.setattr(
            "overload_web.infrastructure.bibs.sierra.SierraBibFetcher", fake_fetcher
        )
        return record_service.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            rules=stub_constants,
        )

    @pytest.fixture
    def stub_service_no_matches(
        self, monkeypatch, library, collection, record_type, stub_constants
    ):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.infrastructure.bibs.sierra.SierraBibFetcher", fake_fetcher
        )
        return record_service.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            rules=stub_constants,
        )

    @pytest.fixture
    def stub_bib_dto(self, library, make_bib_dto):
        dto = make_bib_dto({"020": {"code": "a", "value": "9781234567890"}})
        return dto

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_parse(self, stub_service, stub_bib_dto, caplog):
        records = stub_service.parse(stub_bib_dto.bib.as_marc())
        assert len(records) == 1
        assert str(records[0].bib.library) == str(stub_service.library)
        assert records[0].bib.isbn == "9781234567890"
        assert str(records[0].domain_bib.library) == str(stub_service.library)
        assert records[0].domain_bib.barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.parametrize("record_type", ["full"])
    def test_process_records_full(self, stub_service, stub_bib_dto, template_data):
        original_orders = copy.deepcopy(stub_bib_dto.domain_bib.orders)
        matched_bibs = stub_service.process_records(
            [stub_bib_dto],
            template_data=template_data,
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].domain_bib.orders] == ["j"]

    @pytest.mark.parametrize("record_type", ["order_level"])
    def test_process_records_order_level(
        self, stub_service, stub_bib_dto, template_data
    ):
        original_orders = copy.deepcopy(stub_bib_dto.domain_bib.orders)
        matched_bibs = stub_service.process_records(
            [stub_bib_dto],
            template_data=template_data,
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].domain_bib.orders] == ["b"]

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_process_records_no_matches(self, stub_service_no_matches, stub_bib_dto):
        matched_bibs = stub_service_no_matches.process_records(
            [stub_bib_dto], template_data={}, matchpoints={}
        )
        assert len(matched_bibs) == 1
        assert matched_bibs[0].domain_bib.bib_id is None

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_process_records_vendor_updates(self, stub_service, make_bib_dto):
        dto = make_bib_dto(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(dto.bib)
        matched_bibs = stub_service.process_records(
            [dto], template_data={}, matchpoints={}
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert len(original_bib.get_fields("949")) == 1
        assert len(matched_bibs[0].bib.get_fields("949")) == 2

    @pytest.mark.parametrize("record_type", ["full"])
    def test_process_records_alternate_tags(self, stub_service, make_bib_dto):
        dto = make_bib_dto(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "947": {"code": "a", "value": "B&amp;T SERIES"},
            },
        )
        matched_bibs = stub_service.process_records(
            [dto], template_data={}, matchpoints={}
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_write_marc_binary(self, stub_bib_dto, stub_service, caplog):
        marc_binary = stub_service.write_marc_binary(records=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
