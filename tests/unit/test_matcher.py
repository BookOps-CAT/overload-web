import pytest

from overload_web.bib_records.domain_services import match
from overload_web.errors import OverloadError


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestMatcher:
    def test_match_full(self, fake_fetcher, full_bib):
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        matched_bibs = service.match([full_bib])
        assert len(matched_bibs[0].matches) == 1

    def test_match_full_no_vendor_index(self, fake_fetcher, order_level_bib):
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        setattr(order_level_bib, "record_type", match.bibs.RecordType("cat"))
        assert order_level_bib.vendor_info is None
        with pytest.raises(OverloadError) as exc:
            service.match([order_level_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_order_level(self, fake_fetcher, order_level_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher)
        matched_bibs = service.match(
            [order_level_bib], matchpoints={"primary_matchpoint": "oclc_number"}
        )
        assert len(matched_bibs[0].matches) == 0

    def test_match_order_level_no_matchpoints(self, fake_fetcher, order_level_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher)
        with pytest.raises(TypeError) as exc:
            service.match([order_level_bib])
        assert (
            str(exc.value)
            == "OrderLevelBibMatcher.match() missing 1 required positional argument: 'matchpoints'"
        )
