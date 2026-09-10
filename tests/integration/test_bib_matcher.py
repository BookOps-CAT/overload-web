import pytest

from overload_web.application.pvf import match_service
from overload_web.domain.pvf import models


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


@pytest.fixture
def stub_bib():
    def make_bib(library, collection, record_type):
        return models.DomainBib(
            library=library,
            collection=collection,
            isbn="9781234567890",
            title="Foo",
            record_type=record_type,
            binary_data=b"",
            branch_call_number="Foo",
            research_call_number=["Foo"],
            barcodes=["333331234567890"],
            orders=[],
            update_date="20200101010000.0",
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

    return make_bib


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def acq_bib(request, stub_bib):
    return stub_bib(request.param[0], request.param[1], "acq")


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def cat_bib(request, stub_bib):
    return stub_bib(request.param[0], request.param[1], "cat")


class TestBibMatcher:
    def test_match_full(self, cat_bib, stub_matcher):
        candidates = stub_matcher.match_full_record(cat_bib)
        assert len(candidates) == 1

    def test_match_full_no_candidates(self, stub_matcher_no_matches, cat_bib):
        candidates = stub_matcher_no_matches.match_full_record(cat_bib)
        assert len(candidates) == 0

    def test_match_full_no_vendor_index(self, cat_bib, stub_matcher):
        cat_bib.vendor_info = None
        with pytest.raises(ValueError) as exc:
            stub_matcher.match_full_record(cat_bib)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_order_level(self, acq_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            acq_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 1

    def test_match_order_level_no_matches(self, acq_bib, stub_matcher_no_matches):
        candidates = stub_matcher_no_matches.match_order_record(
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

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", None)]
    )
    def test_review_matches_acq(
        self, stub_bib, stub_matcher, stub_response, library, collection
    ):
        bib2match = stub_bib(library, collection, "acq")
        result = stub_matcher.review_matches(bib2match, matches=[stub_response])
        assert bib2match.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", None)]
    )
    @pytest.mark.parametrize("record_type", ["cat", "sel"])
    def test_review_matches(
        self, stub_bib, stub_matcher, stub_response, library, collection, record_type
    ):
        bib2match = stub_bib(library, collection, record_type)
        result = stub_matcher.review_matches(bib2match, matches=[stub_response])
        assert bib2match.bib_id is None
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
