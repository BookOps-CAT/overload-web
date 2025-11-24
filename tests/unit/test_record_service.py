import copy
import json

import pytest
from bookops_marc import Bib

from overload_web.application import record_service
from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.bib_records.infrastructure import marc, sierra


class StubFetcher(marc_protocols.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def __init__(self, library, collection):
        super().__init__()
        self.library = library
        self.collection = collection

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
class TestRecordProcessingMatcher:
    @pytest.fixture
    def stub_service(self, monkeypatch, library, collection, stub_constants):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher(library, collection)

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.SierraBibFetcher",
            fake_fetcher,
        )
        return record_service.matcher.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library),
            attacher=marc.BookopsMarcUpdater(rules=stub_constants["updater_rules"]),
            reviewer=record_service.reviewer.ReviewedResults(),
        )

    @pytest.fixture
    def stub_service_no_matches(self, monkeypatch, library, collection, stub_constants):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.SierraBibFetcher",
            fake_fetcher,
        )
        return record_service.matcher.BibMatcher(
            fetcher=sierra.SierraBibFetcher(library),
            attacher=marc.BookopsMarcUpdater(rules=stub_constants["updater_rules"]),
            reviewer=record_service.reviewer.ReviewedResults(),
        )

    @pytest.fixture
    def stub_domain_bib(self, library, make_domain_bib):
        dto = make_domain_bib({"020": {"code": "a", "value": "9781234567890"}})
        return dto

    def test_match_and_attach_full(self, stub_service, stub_domain_bib):
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        matched_bibs = stub_service.match_and_attach(
            [stub_domain_bib], record_type=bibs.RecordType.FULL
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].orders] == ["j"]

    def test_match_and_attach_order_level(
        self, stub_service, stub_domain_bib, template_data
    ):
        original_orders = copy.deepcopy(stub_domain_bib.orders)
        matched_bibs = stub_service.match_and_attach(
            [stub_domain_bib],
            template_data=template_data,
            matchpoints={"primary_matchpoint": "isbn"},
            record_type=bibs.RecordType.ORDER_LEVEL,
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].bib_id) == "123"
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in matched_bibs[0].orders] == ["b"]

    def test_match_and_attach_full_no_matches(
        self, stub_service_no_matches, stub_domain_bib
    ):
        matched_bibs = stub_service_no_matches.match_and_attach(
            [stub_domain_bib], record_type=bibs.RecordType.FULL
        )
        assert len(matched_bibs) == 1
        assert matched_bibs[0].bib_id is None

    def test_match_and_attach_order_level_no_matches(
        self, stub_service_no_matches, stub_domain_bib, template_data
    ):
        matched_bibs = stub_service_no_matches.match_and_attach(
            [stub_domain_bib],
            template_data=template_data,
            matchpoints={"primary_matchpoint": "isbn"},
            record_type=bibs.RecordType.ORDER_LEVEL,
        )
        assert len(matched_bibs) == 1
        assert matched_bibs[0].bib_id is None

    def test_match_and_attach_vendor_updates(
        self, stub_service, make_domain_bib, library
    ):
        dto = make_domain_bib(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(Bib(dto.binary_data, library=library))
        matched_bibs = stub_service.match_and_attach(
            [dto], record_type=bibs.RecordType.FULL
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].bib_id) == "123"
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(matched_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    def test_match_and_attach_alternate_tags(self, stub_service, make_domain_bib):
        dto = make_domain_bib(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "947": {"code": "a", "value": "B&amp;T SERIES"},
            },
        )
        matched_bibs = stub_service.match_and_attach(
            [dto], record_type=bibs.RecordType.FULL
        )
        assert len(matched_bibs) == 1
        assert str(matched_bibs[0].bib_id) == "123"


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestRecordProcessingParser:
    @pytest.fixture
    def stub_service(self, library, stub_constants):
        return record_service.parser.BibParser(
            mapper=marc.BookopsMarcMapper(
                rules=stub_constants["mapper_rules"], library=library
            )
        )

    @pytest.fixture
    def stub_domain_bib(self, collection, make_domain_bib):
        dto = make_domain_bib({"020": {"code": "a", "value": "9781234567890"}})
        return dto

    @pytest.mark.parametrize("record_type", ["full", "order_level"])
    def test_parse(self, stub_service, stub_domain_bib, caplog, record_type):
        records = stub_service.parse(
            stub_domain_bib.binary_data, record_type=bibs.RecordType(record_type)
        )
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    def test_serialize(self, stub_domain_bib, stub_service, caplog):
        marc_binary = stub_service.serialize(records=[stub_domain_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
