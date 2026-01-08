import pytest

from overload_web.bib_records.domain_services import match
from overload_web.errors import OverloadError


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestMatcher:
    def test_match_order_level(self, fake_fetcher, acq_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher)
        matched_bibs = service.match(
            [acq_bib], matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(matched_bibs[0].matches) == 4

    def test_match_order_level_no_matches(self, fake_fetcher_no_matches, acq_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher_no_matches)
        matched_bibs = service.match(
            [acq_bib],
            matchpoints={
                "primary_matchpoint": "oclc_number",
                "secondary_matchpoint": "isbn",
            },
        )
        assert len(matched_bibs[0].matches) == 0

    def test_match_order_level_no_matchpoints(self, fake_fetcher, acq_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher)
        with pytest.raises(TypeError) as exc:
            service.match([acq_bib])
        assert (
            str(exc.value)
            == "OrderLevelBibMatcher.match() missing 1 required positional argument: 'matchpoints'"
        )

    def test_match_full(self, fake_fetcher, cat_bib):
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        matched_bibs = service.match([cat_bib])
        assert len(matched_bibs[0].matches) == 4

    def test_match_full_no_matches(self, fake_fetcher_no_matches, cat_bib):
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher_no_matches)
        matched_bibs = service.match([cat_bib])
        assert len(matched_bibs[0].matches) == 0

    def test_match_full_no_vendor_index(self, fake_fetcher, acq_bib):
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        setattr(acq_bib, "record_type", match.bibs.RecordType("cat"))
        assert acq_bib.vendor_info is None
        with pytest.raises(OverloadError) as exc:
            service.match([acq_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_full_alternate_tags(self, fake_fetcher, make_domain_bib):
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        dto = make_domain_bib({"947": {"code": "a", "value": "B&amp;T SERIES"}}, "cat")
        matched_bibs = service.match([dto])
        assert len(matched_bibs[0].matches) == 4
