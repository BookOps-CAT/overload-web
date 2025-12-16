import json

import pytest

from overload_web.bib_records.domain import marc_protocols
from overload_web.bib_records.domain_services import matcher
from overload_web.bib_records.infrastructure.sierra import clients, responses
from overload_web.errors import OverloadError


class StubFetcher(marc_protocols.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def __init__(self, library, collection):
        super().__init__()
        self.library = library
        self.collection = collection

    def get_bibs_by_id(self, value, key):
        if str(self.library) == "nypl":
            file = f"tests/data/{str(self.library)}_{str(self.collection)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["data"]
            return [responses.NYPLPlatformResponse(data=i) for i in data]
        else:
            file = f"tests/data/{str(self.library)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["response"]["docs"]
            return [responses.BPLSolrResponse(data=i) for i in data]


@pytest.fixture
def stub_full_bib(make_full_bib):
    dto = make_full_bib({"020": {"code": "a", "value": "9781234567890"}})
    return dto


@pytest.fixture
def stub_order_bib(make_order_bib):
    dto = make_order_bib({"020": {"code": "a", "value": "9781234567890"}})
    return dto


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestMatcher:
    @pytest.fixture
    def stub_full_record_service(self, monkeypatch, library, collection):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher(library, collection)

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.clients.SierraBibFetcher",
            fake_fetcher,
        )
        return matcher.BibMatcher(
            fetcher=clients.SierraBibFetcher(library),
            strategy=clients.MatchStrategyFactory().make("cat"),
        )

    @pytest.fixture
    def stub_order_record_service(self, monkeypatch, library, collection):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher(library, collection)

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.clients.SierraBibFetcher",
            fake_fetcher,
        )
        return matcher.BibMatcher(
            fetcher=clients.SierraBibFetcher(library),
            strategy=clients.MatchStrategyFactory().make("acq"),
        )

    @pytest.fixture
    def stub_full_record_service_no_matches(self, monkeypatch, library):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.clients.SierraBibFetcher",
            fake_fetcher,
        )
        return matcher.BibMatcher(
            fetcher=clients.SierraBibFetcher(library),
            strategy=clients.MatchStrategyFactory().make("cat"),
        )

    @pytest.fixture
    def stub_order_record_service_no_matches(self, monkeypatch, library):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.clients.SierraBibFetcher",
            fake_fetcher,
        )
        return matcher.BibMatcher(
            fetcher=clients.SierraBibFetcher(library),
            strategy=clients.MatchStrategyFactory().make("acq"),
        )

    def test_match_full(self, stub_full_record_service, stub_full_bib):
        matched_bibs = stub_full_record_service.match([stub_full_bib])
        assert len(matched_bibs[0].matches) == 4

    def test_match_full_no_matches(
        self, stub_full_record_service_no_matches, stub_full_bib
    ):
        matched_bibs = stub_full_record_service_no_matches.match([stub_full_bib])
        assert len(matched_bibs[0].matches) == 0

    def test_match_full_no_vendor_index(self, stub_full_record_service, stub_order_bib):
        with pytest.raises(OverloadError) as exc:
            stub_full_record_service.match([stub_order_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_full_alternate_tags(self, stub_full_record_service, make_full_bib):
        dto = make_full_bib(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "947": {"code": "a", "value": "B&amp;T SERIES"},
            },
        )
        matched_bibs = stub_full_record_service.match([dto])
        assert len(matched_bibs[0].matches) == 4

    def test_match_order_level(self, stub_order_record_service, stub_order_bib):
        matched_bibs = stub_order_record_service.match(
            [stub_order_bib], matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(matched_bibs[0].matches) == 4

    def test_match_order_level_no_matches(
        self, stub_order_record_service_no_matches, stub_order_bib
    ):
        matched_bibs = stub_order_record_service_no_matches.match(
            [stub_order_bib], matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(matched_bibs[0].matches) == 0

    def test_match_order_level_no_matchpoints(
        self, stub_order_record_service, stub_order_bib
    ):
        with pytest.raises(OverloadError) as exc:
            stub_order_record_service.match([stub_order_bib])
        assert (
            str(exc.value)
            == "Matchpoints from order template required for acquisition or selection workflow."
        )
