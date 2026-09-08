import pytest

from overload_web.application.pvf import match_service


@pytest.fixture
def stub_matcher(fake_fetcher):
    return match_service.BibMatcher(fetcher=fake_fetcher)


@pytest.mark.parametrize(
    "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", None)]
)
class TestBibMatcher:
    def test_match_full(self, full_bib, stub_matcher):
        candidates = stub_matcher.match_full_record(full_bib)
        assert len(candidates) == 1

    def test_match_full_no_candidates(self, fake_fetcher_no_matches, full_bib):
        service = match_service.BibMatcher(fetcher=fake_fetcher_no_matches)
        candidates = service.match_full_record(full_bib)
        assert len(candidates) == 0

    def test_match_full_no_vendor_index(self, full_bib, stub_matcher):
        full_bib.vendor_info = None
        with pytest.raises(ValueError) as exc:
            stub_matcher.match_full_record(full_bib)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_order_level(self, acq_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            acq_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 1

    def test_match_order_level_no_matches(self, acq_bib, fake_fetcher_no_matches):
        service = match_service.BibMatcher(fetcher=fake_fetcher_no_matches)
        candidates = service.match_order_record(
            acq_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 0

    def test_match_order_level_matchpoint_none(self, acq_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            acq_bib, matchpoints={"primary_matchpoint": None}
        )
        assert len(candidates) == 0

    def test_match_order_level_no_matchpoints(self, acq_bib, stub_matcher):
        with pytest.raises(TypeError) as exc:
            stub_matcher.match_order_record(acq_bib)
        assert (
            str(exc.value)
            == "BibMatcher.match_order_record() missing 1 required positional argument: 'matchpoints'"
        )

    def test_review_matches_acq(self, acq_bib, stub_matcher, sierra_response):
        result = stub_matcher.review_matches(acq_bib, matches=[sierra_response])
        assert acq_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == result.call_number

    def test_review_matches_cat(self, full_bib, stub_matcher, sierra_response):
        result = stub_matcher.review_matches(bib=full_bib, matches=[sierra_response])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_title == "Record 1"

    def test_review_matches_sel(self, sel_bib, stub_matcher, sierra_response):
        result = stub_matcher.review_matches(sel_bib, matches=[sierra_response])
        assert sel_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == result.call_number
