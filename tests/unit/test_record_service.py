import copy
import json

import pytest

from overload_web.application import record_service
from overload_web.bib_records.domain import marc_protocols


class StubFetcher(marc_protocols.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def __init__(self, library, collection, record_type):
        super().__init__()
        self.library = library
        self.collection = collection
        self.record_type = record_type

    def get_bibs_by_id(self, value, key):
        with open("tests/data/process_bibs_results.json", "r", encoding="utf-8") as fh:
            bibs = json.loads(fh.read())
        results = bibs["results"]
        for result in results:
            result["collection"] = str(self.collection)
            if str(self.collection) == "RL":
                result["research_call_number"] = result["call_number"]
            elif str(self.collection) == "BL" or str(self.library) == "BPL":
                result["branch_call_number"] = result["call_number"]
            else:
                result["branch_call_number"] = result["call_number"]
                result["research_call_number"] = result["call_number"]
            result.pop("call_number", None)
        return results


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
            return FakeBibFetcher(library, collection, record_type)

        monkeypatch.setattr(
            "overload_web.application.record_service.sierra.SierraBibFetcher",
            fake_fetcher,
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
            "overload_web.application.record_service.sierra.SierraBibFetcher",
            fake_fetcher,
        )
        return record_service.RecordProcessingService(
            library=library,
            collection=collection,
            record_type=record_type,
            rules=stub_constants,
        )

    @pytest.fixture
    def stub_bib_dto(self, library, make_bib_dto, collection):
        dto = make_bib_dto({"020": {"code": "a", "value": "9781234567890"}})
        return dto

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_parse(self, stub_service, stub_bib_dto, caplog):
        records = stub_service.parser.parse(stub_bib_dto.bib.as_marc())
        assert len(records) == 1
        assert str(records[0].bib.library) == str(stub_service.library)
        assert records[0].bib.isbn == "9781234567890"
        assert str(records[0].domain_bib.library) == str(stub_service.library)
        assert records[0].domain_bib.barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.parametrize("record_type", ["full"])
    def test_match_and_attach_full(self, stub_service, stub_bib_dto, template_data):
        original_orders = copy.deepcopy(stub_bib_dto.domain_bib.orders)
        matched_bibs = stub_service.matcher.match_and_attach(
            [stub_bib_dto],
            template_data=template_data,
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].domain_bib.orders] == ["j"]

    @pytest.mark.parametrize("record_type", ["order_level"])
    def test_match_and_attach_order_level(
        self, stub_service, stub_bib_dto, template_data
    ):
        original_orders = copy.deepcopy(stub_bib_dto.domain_bib.orders)
        matched_bibs = stub_service.matcher.match_and_attach(
            [stub_bib_dto],
            template_data=template_data,
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].domain_bib.orders] == ["b"]

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_match_and_attach_no_matches(self, stub_service_no_matches, stub_bib_dto):
        matched_bibs = stub_service_no_matches.matcher.match_and_attach(
            [stub_bib_dto], template_data={}, matchpoints={}
        )
        assert len(matched_bibs) == 1
        assert matched_bibs[0].domain_bib.bib_id is None

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_match_and_attach_vendor_updates(self, stub_service, make_bib_dto):
        dto = make_bib_dto(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(dto.bib)
        matched_bibs = stub_service.matcher.match_and_attach(
            [dto], template_data={}, matchpoints={}
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"
        assert len(original_bib.get_fields("949")) == 1
        assert len(matched_bibs[0].bib.get_fields("949")) == 2

    @pytest.mark.parametrize("record_type", ["full"])
    def test_match_and_attach_alternate_tags(self, stub_service, make_bib_dto):
        dto = make_bib_dto(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "947": {"code": "a", "value": "B&amp;T SERIES"},
            },
        )
        matched_bibs = stub_service.matcher.match_and_attach(
            [dto], template_data={}, matchpoints={}
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].domain_bib.bib_id) == "123"

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_serialize(self, stub_bib_dto, stub_service, caplog):
        marc_binary = stub_service.parser.serialize(records=[stub_bib_dto])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
