import pytest

from overload_web.bib_records.domain_models import bibs
from overload_web.bib_records.domain_services import match
from overload_web.errors import OverloadError


@pytest.fixture
def stub_domain_bib(library, collection):
    return bibs.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type="acq",
        binary_data=b"",
    )


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestMatcher:
    def test_match_full(self, fake_fetcher, stub_domain_bib):
        stub_domain_bib.vendor_info = bibs.VendorInfo(
            name="UNKNOWN",
            matchpoints={
                "primary_matchpoint": "isbn",
                "secondary_matchpoint": "oclc_number",
            },
            bib_fields=[],
        )
        stub_domain_bib.record_type = "cat"
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        matched_bibs = service.match([stub_domain_bib])
        assert len(matched_bibs[0].matches) == 1

    def test_match_full_no_vendor_index(self, fake_fetcher, stub_domain_bib):
        stub_domain_bib.record_type = "cat"
        service = match.FullLevelBibMatcher(fetcher=fake_fetcher)
        assert stub_domain_bib.vendor_info is None
        with pytest.raises(OverloadError) as exc:
            service.match([stub_domain_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_order_level(self, fake_fetcher, stub_domain_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher)
        matched_bibs = service.match(
            [stub_domain_bib], matchpoints={"primary_matchpoint": "oclc_number"}
        )
        assert len(matched_bibs[0].matches) == 0

    def test_match_order_level_no_matchpoints(self, fake_fetcher, stub_domain_bib):
        service = match.OrderLevelBibMatcher(fetcher=fake_fetcher)
        with pytest.raises(TypeError) as exc:
            service.match([stub_domain_bib])
        assert (
            str(exc.value)
            == "OrderLevelBibMatcher.match() missing 1 required positional argument: 'matchpoints'"
        )
