from contextlib import nullcontext as does_not_raise

import pytest

from overload_web.application.services import match_service
from overload_web.domain.errors import OverloadError
from overload_web.domain.models import bibs
from overload_web.infrastructure import clients


@pytest.fixture
def stub_domain_bib(library, collection):
    return bibs.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type="acq",
        binary_data=b"",
        oclc_number=["12345", "67890"],
    )


class TestSierraBibFetcher:
    @pytest.mark.parametrize("match", ["upc", "isbn"])
    def test_get_bibs_by_id_bpl(self, mock_session, match, caplog):
        fetcher = clients.SierraBibFetcher(session=clients.BPLSolrSession())
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert "Querying Sierra with BPLSolrSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "BPLSolrSession"

    @pytest.mark.parametrize("id", [".b123", ".i123", ".o123", "123", 123, 123456789])
    def test_get_bibs_by_bib_id_bpl(self, mock_session, id, caplog):
        """Test `_prep_sierra_number override."""
        fetcher = clients.SierraBibFetcher(session=clients.BPLSolrSession())
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    @pytest.mark.parametrize(
        "num, norm",
        [
            ("on1234567890", "on1234567890"),
            ("123456789", "ocn123456789"),
            (123, "ocm00000123"),
            ("1234567890", "on1234567890"),
        ],
    )
    def test_get_bibs_by_oclc_number_bpl(self, mock_session, num, norm, caplog):
        fetcher = clients.SierraBibFetcher(session=clients.BPLSolrSession())
        fetcher.get_bibs_by_id(value=num, key="oclc_number")
        assert (
            caplog.records[0].msg
            == f"Querying Sierra with BPLSolrSession on oclc_number with value: {norm}."
        )

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_by_id_nypl(self, mock_session, match, caplog):
        fetcher = clients.SierraBibFetcher(session=clients.NYPLPlatformSession())
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert "Querying Sierra with NYPLPlatformSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "NYPLPlatformSession"

    @pytest.mark.parametrize("id", [".b123", ".i123", ".o123", "123", 123, 123456789])
    def test_get_bibs_by_bib_id_nypl(self, mock_session, id, caplog):
        """Test `_prep_sierra_number override."""
        fetcher = clients.SierraBibFetcher(session=clients.NYPLPlatformSession())
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    @pytest.mark.parametrize(
        "num, norm",
        [
            ("on1234567890", "1234567890"),
            ("ocn123456789", "123456789"),
            ("ocm00000123", "123"),
            (123, "123"),
        ],
    )
    def test_get_bibs_by_oclc_number_nypl(self, mock_session, num, norm, caplog):
        fetcher = clients.SierraBibFetcher(session=clients.NYPLPlatformSession())
        fetcher.get_bibs_by_id(value=num, key="oclc_number")
        assert (
            caplog.records[0].msg
            == f"Querying Sierra with NYPLPlatformSession on oclc_number with value: {norm}."
        )

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert "Unsupported query matchpoint: 'bar'" in caplog.text
        assert "Invalid matchpoint: 'bar'. Available matchpoints are:" in str(exc.value)

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id_no_value_passed(self, match, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        bibs = fetcher.get_bibs_by_id(value=None, key=match)
        assert bibs == []
        assert f"Skipping Sierra query on {match} with missing value." in caplog.text

    def test_get_bibs_by_id_nypl_error(self, mock_nypl_session_error, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_nypl_session_error)
        with pytest.raises(clients.BookopsPlatformError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsPlatformError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_bpl_error(self, mock_bpl_session_error, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_bpl_session_error)
        with pytest.raises(clients.BookopsSolrError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsSolrError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_nypl_issn(self, mock_session):
        fetcher = clients.SierraBibFetcher(session=clients.NYPLPlatformSession())
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in NYPL Platform" in str(exc.value)

    def test_get_bibs_by_id_bpl_issn(self, mock_session):
        fetcher = clients.SierraBibFetcher(session=clients.BPLSolrSession())
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in BPL Solr" in str(exc.value)


@pytest.mark.parametrize(
    "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
)
class TestBibMatcher:
    @pytest.mark.parametrize(
        "matchpoints",
        [{"primary_matchpoint": "isbn"}, {"primary_matchpoint": "oclc_number"}],
    )
    def test_match_full(self, fake_fetcher, stub_domain_bib, matchpoints):
        stub_domain_bib.vendor_info = bibs.VendorInfo(
            name="UNKNOWN", matchpoints=matchpoints, bib_fields=[]
        )
        stub_domain_bib.record_type = "cat"
        service = match_service.BibMatcher(fetcher=fake_fetcher)
        candidates = service.match_full_record(stub_domain_bib)
        assert len(candidates) == 1

    @pytest.mark.parametrize(
        "matchpoints",
        [{"primary_matchpoint": "isbn"}, {"primary_matchpoint": "oclc_number"}],
    )
    def test_match_full_no_candidates(
        self, fake_fetcher_no_matches, stub_domain_bib, matchpoints
    ):
        stub_domain_bib.vendor_info = bibs.VendorInfo(
            name="UNKNOWN", matchpoints=matchpoints, bib_fields=[]
        )
        stub_domain_bib.record_type = "cat"
        service = match_service.BibMatcher(fetcher=fake_fetcher_no_matches)
        candidates = service.match_full_record(stub_domain_bib)
        assert len(candidates) == 0

    def test_match_full_no_vendor_index(self, fake_fetcher, stub_domain_bib):
        stub_domain_bib.record_type = "cat"
        service = match_service.BibMatcher(fetcher=fake_fetcher)
        assert stub_domain_bib.vendor_info is None
        with pytest.raises(OverloadError) as exc:
            service.match_full_record(stub_domain_bib)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_order_level(self, fake_fetcher, stub_domain_bib):
        service = match_service.BibMatcher(fetcher=fake_fetcher)
        candidates = service.match_order_record(
            stub_domain_bib, matchpoints={"primary_matchpoint": "upc"}
        )
        assert len(candidates) == 0

    def test_match_order_level_no_matchpoints(self, fake_fetcher, stub_domain_bib):
        service = match_service.BibMatcher(fetcher=fake_fetcher)
        with pytest.raises(TypeError) as exc:
            service.match_order_record(stub_domain_bib)
        assert (
            str(exc.value)
            == "BibMatcher.match_order_record() missing 1 required positional argument: 'matchpoints'"
        )

    def test_match_order_level_none(self, fake_fetcher, stub_domain_bib):
        service = match_service.BibMatcher(fetcher=fake_fetcher)
        candidates = service.match_order_record(
            stub_domain_bib, matchpoints={"primary_matchpoint": None}
        )
        assert len(candidates) == 0
