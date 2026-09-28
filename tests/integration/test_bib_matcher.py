import pytest

from overload_web.application.pvf import match_service


@pytest.fixture
def stub_response(library, collection):
    isbns = ["9781234567890"]
    title = "Record 1"
    id = "12345"
    call_no = "Foo"
    control_no = "ocn123456789"
    if library == "bpl":
        return {
            "call_number": call_no,
            "id": id,
            "isbn": isbns,
            "sm_bib_varfields": ["005 || 20200101000001.0", "024 || {{a}} 12345"],
            "sm_item_data": ['{"barcode": "33333123456789"}'],
            "ss_marc_tag_001": control_no,
            "ss_marc_tag_003": "OCoLC",
            "ss_marc_tag_005": "20000101010000.0",
            "title": title,
        }
    if collection == "RL":
        tag = "852"
        ind1 = "8"
    else:
        tag = "091"
        ind1 = " "
    return {
        "id": id,
        "controlNumber": control_no,
        "standardNumbers": isbns,
        "title": title,
        "updatedDate": "2000-01-01T01:00:00",
        "varFields": [
            {
                "marcTag": tag,
                "ind1": ind1,
                "ind2": " ",
                "subfields": [{"content": call_no, "tag": "a"}],
            },
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]},
        ],
    }


@pytest.fixture
def stub_matcher(fake_fetcher):
    return match_service.BibMatcher(fetcher=fake_fetcher)


@pytest.fixture
def stub_matcher_no_matches(fake_fetcher, monkeypatch):
    def empty_response(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "overload_web.infrastructure.sierra_clients.SierraBibFetcher.get_bibs_by_id",
        empty_response,
    )
    return match_service.BibMatcher(fetcher=fake_fetcher)


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_bib(stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    return stub_bib(request.param[0], request.param[1], record_type)


class TestBibMatcher:
    @pytest.mark.workflow(record_type="cat")
    def test_match_full(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_full_record(mock_bib)
        assert len(candidates) == 1

    @pytest.mark.workflow(record_type="cat")
    def test_match_full_no_candidates(self, stub_matcher_no_matches, mock_bib):
        candidates = stub_matcher_no_matches.match_full_record(mock_bib)
        assert len(candidates) == 0

    @pytest.mark.workflow(record_type="cat")
    def test_match_full_no_vendor_index(self, mock_bib, stub_matcher):
        mock_bib.vendor_info = None
        with pytest.raises(ValueError) as exc:
            stub_matcher.match_full_record(mock_bib)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            mock_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 1

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level_no_matches(self, mock_bib, stub_matcher_no_matches):
        candidates = stub_matcher_no_matches.match_order_record(
            mock_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level_matchpoint_none(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            mock_bib, matchpoints={"primary_matchpoint": None}
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level_no_matchpoints(self, mock_bib, stub_matcher):
        with pytest.raises(TypeError) as exc:
            stub_matcher.match_order_record(mock_bib)
        assert (
            str(exc.value)
            == "BibMatcher.match_order_record() missing 1 required positional argument: 'matchpoints'"
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", None)]
    )
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_review_matches(
        self, stub_bib, stub_matcher, stub_response, library, collection, record_type
    ):
        bib2match = stub_bib(library, collection, record_type)
        result = stub_matcher.review_matches(bib2match, matches=[stub_response])
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
