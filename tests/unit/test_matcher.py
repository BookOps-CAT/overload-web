import json

import pytest

from overload_web.bib_records.domain_models import (
    marc_protocols,
    sierra_responses,
)
from overload_web.bib_records.domain_services import match
from overload_web.bib_records.infrastructure import clients
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
            return [sierra_responses.NYPLPlatformResponse(data=i) for i in data]
        else:
            file = f"tests/data/{str(self.library)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["response"]["docs"]
            return [sierra_responses.BPLSolrResponse(data=i) for i in data]


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestMatcher:
    @pytest.fixture
    def stub_fetcher(self, monkeypatch, library, collection):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher(library, collection)

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.clients.SierraBibFetcher",
            fake_fetcher,
        )
        return clients.SierraBibFetcher(library)

    @pytest.fixture
    def stub_fetcher_no_matches(self, monkeypatch, library):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.clients.SierraBibFetcher",
            fake_fetcher,
        )
        return clients.SierraBibFetcher(library)

    def test_match_order_level(self, stub_fetcher, stub_acq_bib):
        service = match.OrderLevelBibMatcher(fetcher=stub_fetcher)
        matched_bibs = service.match(
            [stub_acq_bib], matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(matched_bibs[0].matches) == 4

    def test_match_order_level_no_matches(self, stub_fetcher_no_matches, stub_acq_bib):
        service = match.OrderLevelBibMatcher(fetcher=stub_fetcher_no_matches)
        matched_bibs = service.match(
            [stub_acq_bib],
            matchpoints={
                "primary_matchpoint": "oclc_number",
                "secondary_matchpoint": "isbn",
            },
        )
        assert len(matched_bibs[0].matches) == 0

    def test_match_order_level_no_matchpoints(self, stub_fetcher, stub_acq_bib):
        service = match.OrderLevelBibMatcher(fetcher=stub_fetcher)
        with pytest.raises(TypeError) as exc:
            service.match([stub_acq_bib])
        assert (
            str(exc.value)
            == "OrderLevelBibMatcher.match() missing 1 required positional argument: 'matchpoints'"
        )

    def test_match_full(self, stub_fetcher, stub_cat_bib):
        service = match.FullLevelBibMatcher(fetcher=stub_fetcher)
        matched_bibs = service.match([stub_cat_bib])
        assert len(matched_bibs[0].matches) == 4

    def test_match_full_no_matches(self, stub_fetcher_no_matches, stub_cat_bib):
        service = match.FullLevelBibMatcher(fetcher=stub_fetcher_no_matches)
        matched_bibs = service.match([stub_cat_bib])
        assert len(matched_bibs[0].matches) == 0

    def test_match_full_no_vendor_index(self, stub_fetcher, stub_acq_bib):
        service = match.FullLevelBibMatcher(fetcher=stub_fetcher)
        setattr(stub_acq_bib, "record_type", match.bibs.RecordType("cat"))
        assert stub_acq_bib.vendor_info is None
        with pytest.raises(OverloadError) as exc:
            service.match([stub_acq_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_full_alternate_tags(self, stub_fetcher, make_domain_bib):
        service = match.FullLevelBibMatcher(fetcher=stub_fetcher)
        dto = make_domain_bib({"947": {"code": "a", "value": "B&amp;T SERIES"}}, "cat")
        matched_bibs = service.match([dto])
        assert len(matched_bibs[0].matches) == 4
