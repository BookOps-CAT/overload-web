import pytest

from overload_web.domain.pvf import models, services
from overload_web.infrastructure import sierra_clients


@pytest.fixture
def mock_bib(request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]
    return models.DomainBib(
        library=marker.kwargs["library"],
        collection=marker.kwargs["collection"],
        isbn="9781234567890",
        title="Foo",
        record_type=record_type,
        binary_data=b"",
        orders=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN",
            bib_fields=[],
            matchpoints={
                "primary_matchpoint": "isbn",
                "secondary_matchpoint": "control_number",
            },
        ),
        parsed_fields=[],
    )


@pytest.fixture
def stub_fetcher(mock_sierra_session):
    return sierra_clients.SierraBibFetcher(session=mock_sierra_session)


@pytest.fixture
def mock_sierra_no_matches(mock_sierra_session, monkeypatch):
    fake_fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)

    def empty_response(*args, **kwargs):
        return []

    monkeypatch.setattr(
        sierra_clients.SierraBibFetcher, "get_bibs_by_id", empty_response
    )
    return fake_fetcher


@pytest.fixture
def stub_matcher(mock_sierra_session):
    return services.BibMatcher(fetcher_factory=sierra_clients.FetcherFactory.make)


@pytest.fixture
def stub_matcher_no_matches(monkeypatch, mock_sierra_session):
    def empty_response(*args, **kwargs):
        return []

    monkeypatch.setattr(
        sierra_clients.SierraBibFetcher, "get_bibs_by_id", empty_response
    )
    return services.BibMatcher(fetcher_factory=sierra_clients.FetcherFactory.make)


class TestBibMatcher:
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_match_full(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_full_record(record=mock_bib, library="nypl")
        assert len(candidates) == 1

    @pytest.mark.workflow(library="bpl", collection=None, record_type="cat")
    def test_match_full_no_candidates(self, stub_matcher_no_matches, mock_bib):
        candidates = stub_matcher_no_matches.match_full_record(
            record=mock_bib, library="bpl"
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="cat")
    def test_match_full_no_vendor_index(self, mock_bib, stub_matcher):
        mock_bib.vendor_info = None
        with pytest.raises(ValueError) as exc:
            stub_matcher.match_full_record(record=mock_bib, library="nypl")
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    @pytest.mark.workflow(library="bpl", collection=None, record_type="acq")
    def test_match_order_level(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            record=mock_bib, matchpoints={"primary_matchpoint": "isbn"}, library="bpl"
        )
        assert len(candidates) == 1

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="acq")
    def test_match_order_level_no_matches(self, mock_bib, stub_matcher_no_matches):
        candidates = stub_matcher_no_matches.match_order_record(
            record=mock_bib, matchpoints={"primary_matchpoint": "isbn"}, library="nypl"
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="acq")
    def test_match_order_level_matchpoint_none(self, mock_bib, stub_matcher_no_matches):
        candidates = stub_matcher_no_matches.match_order_record(
            record=mock_bib, matchpoints={"primary_matchpoint": None}, library="nypl"
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="acq")
    def test_match_order_level_no_matchpoints(self, mock_bib, stub_matcher_no_matches):
        with pytest.raises(TypeError) as exc:
            stub_matcher_no_matches.match_order_record(record=mock_bib, library="nypl")
        assert (
            str(exc.value)
            == "BibMatcher.match_order_record() missing 1 required positional argument: 'matchpoints'"
        )

    @pytest.mark.workflow(library="bpl", collection=None, record_type="acq")
    def test_review_matches(self, mock_bib, stub_matcher):
        reviewed = stub_matcher.review_matches(bib=mock_bib, matches=[])
        assert reviewed.target_bib_id is None
