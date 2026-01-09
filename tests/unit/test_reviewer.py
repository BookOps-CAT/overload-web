import datetime

import pytest

from overload_web.bib_records.domain_models import sierra_responses
from overload_web.bib_records.domain_services import review


@pytest.fixture
def nypl_data():
    call_no = {"content": "Foo", "tag": "a"}
    return {
        "id": "12345",
        "title": "Record 1",
        "updatedDate": "2000-01-01T01:00:00",
        "varFields": [
            {"marcTag": "091", "subfields": [call_no]},
            {"marcTag": "852", "ind1": "8", "ind2": " ", "subfields": [call_no]},
        ],
    }


class TestReviewer:
    @pytest.mark.parametrize(
        "library, collection",
        [
            ("nypl", "BL"),
            ("nypl", "RL"),
            ("bpl", "NONE"),
        ],
    )
    def test_base_analyzer(self, acq_bib, sierra_response, library, collection):
        service = review.BaseMatchAnalyzer()
        with pytest.raises(NotImplementedError):
            service.resolve(acq_bib, candidates=[sierra_response])

    @pytest.mark.parametrize(
        "library, collection",
        [
            ("nypl", "BL"),
            ("nypl", "RL"),
            ("bpl", "NONE"),
        ],
    )
    def test_attach_acq(self, acq_bib, sierra_response):
        acq_response = sierra_responses.MatcherResponse(
            bib=acq_bib, matches=[sierra_response]
        )
        service = review.AcquisitionsMatchAnalyzer()
        attached_bibs = service.review_candidates([acq_response])
        assert attached_bibs[1][0].bib_id is None
        assert acq_response.bib.bib_id is None

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_attach_cat_bpl(self, cat_bib, sierra_response):
        cat_response = sierra_responses.MatcherResponse(
            bib=cat_bib, matches=[sierra_response]
        )
        service = review.BPLCatMatchAnalyzer()
        attached_bibs = service.review_candidates([cat_response])
        assert attached_bibs[1][0].bib_id == "12345"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_attach_cat_nypl_bl(self, cat_bib, sierra_response):
        cat_response = sierra_responses.MatcherResponse(
            bib=cat_bib, matches=[sierra_response]
        )
        service = review.NYPLCatBranchMatchAnalyzer()
        attached_bibs = service.review_candidates([cat_response])
        assert attached_bibs[1][0].bib_id == "12345"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_attach_cat_nypl_rl(self, cat_bib, sierra_response):
        cat_response = sierra_responses.MatcherResponse(
            bib=cat_bib, matches=[sierra_response]
        )
        service = review.NYPLCatResearchMatchAnalyzer()
        attached_bibs = service.review_candidates([cat_response])
        assert attached_bibs[1][0].bib_id == "12345"

    @pytest.mark.parametrize(
        "library, collection",
        [
            ("nypl", "BL"),
            ("nypl", "RL"),
            ("bpl", "NONE"),
        ],
    )
    def test_attach_sel(self, sel_bib, sierra_response):
        sel_response = sierra_responses.MatcherResponse(
            bib=sel_bib, matches=[sierra_response]
        )
        service = review.SelectionMatchAnalyzer()
        attached_bibs = service.review_candidates([sel_response])
        assert attached_bibs[1][0].bib_id == "12345"


class TestCandidateClassifier:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_bpl(self, sierra_response, cat_bib):
        cat_bib.isbn = None
        classified = review.CandidateClassifier.classify(
            cat_bib, candidates=[sierra_response, sierra_response]
        )
        assert cat_bib.bib_id is None
        assert classified.duplicates == ["12345", "12345"]
        assert sierra_response.bib_id == "12345"
        assert sierra_response.barcodes == ["33333123456789"]
        assert sierra_response.branch_call_number == "Foo"
        assert sierra_response.cat_source == "inhouse"
        assert sierra_response.collection is None
        assert sierra_response.control_number == "ocn123456789"
        assert sierra_response.isbn == ["9781234567890"]
        assert sierra_response.oclc_number == ["ocn123456789"]
        assert sierra_response.research_call_number == []
        assert sierra_response.upc == []
        assert sierra_response.update_date == "20000101010000.0"
        assert sierra_response.update_datetime == datetime.datetime(
            2000, 1, 1, 1, 0, 0, 0
        )
        assert sierra_response.var_fields == [
            {"marc_tag": "099", "subfields": [{"tag": "a", "content": "Foo"}]}
        ]
        assert review.get_resource_id(cat_bib) is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_nypl(self, sierra_response, cat_bib, collection):
        cat_bib.isbn = None
        classified = review.CandidateClassifier.classify(
            cat_bib, candidates=[sierra_response, sierra_response]
        )
        assert cat_bib.bib_id is None
        assert classified.duplicates == ["12345", "12345"]
        assert sierra_response.bib_id == "12345"
        assert sierra_response.barcodes == []
        assert sierra_response.branch_call_number == "Foo"
        assert sierra_response.cat_source == "inhouse"
        assert sierra_response.collection == collection
        assert sierra_response.control_number == "ocn123456789"
        assert sierra_response.isbn == ["9781234567890"]
        assert sierra_response.oclc_number == ["ocn123456789"]
        assert sierra_response.research_call_number == ["Foo"]
        assert sierra_response.upc == []
        assert sierra_response.update_date == "2000-01-01T01:00:00"
        assert sierra_response.update_datetime == datetime.datetime(
            2000, 1, 1, 1, 0, 0, 0
        )
        assert len(sierra_response.var_fields) == 4
        assert review.get_resource_id(cat_bib) is None

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_resolve_no_results(self, cat_bib):
        classified = review.CandidateClassifier.classify(cat_bib, candidates=[])
        assert classified.duplicates == []

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    @pytest.mark.parametrize("key", ["control_number", "oclc_number", "upc"])
    def test_resolve_resource_id(self, cat_bib, key):
        cat_bib.isbn = None
        setattr(cat_bib, key, "987654321")
        resource_id = review.get_resource_id(cat_bib)
        assert resource_id == "987654321"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_mixed(self, cat_bib, nypl_data):
        nypl_data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
        )
        nypl_data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        )
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        classified = review.CandidateClassifier.classify(cat_bib, candidates=[response])
        assert len(classified.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_unmatched(self, cat_bib, sierra_response):
        cat_bib.collection = "NONE"
        classified = review.CandidateClassifier.classify(
            cat_bib, candidates=[sierra_response]
        )

        assert len(classified.other) == 1
        assert len(classified.matched) == 0


class TestSelectionMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_resolve(self, sierra_response, cat_bib):
        reviewer = review.SelectionMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[sierra_response])
        assert cat_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.resource_id == "9781234567890"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_no_call_no(self, cat_bib, collection, nypl_data):
        nypl_data["varFields"] = [
            {
                "marcTag": "910",
                "subfields": [{"content": collection, "tag": "a"}],
            }
        ]
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        reviewer = review.SelectionMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert cat_bib.bib_id is None
        assert response.bib_id == "12345"
        assert response.branch_call_number is None
        assert response.research_call_number == []
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_resolve_no_results(self, cat_bib):
        reviewer = review.SelectionMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[])
        assert cat_bib.bib_id is None
        assert result.target_bib_id is None


class TestAcquisitionsMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_resolve(self, sierra_response, cat_bib):
        reviewer = review.AcquisitionsMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[sierra_response])
        assert cat_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []


class TestNYPLCatBranchMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve(self, sierra_response, cat_bib):
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[sierra_response])
        assert cat_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_no_results(self, cat_bib):
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[])
        assert cat_bib.bib_id is None
        assert result.target_bib_id is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_vendor_record(self, cat_bib, nypl_data):
        data = {k: v for k, v in nypl_data.items()}
        data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
        )
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "12345"
        assert response.update_datetime < cat_bib.update_datetime

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_no_call_no_match_inhouse(self, cat_bib):
        data = {
            "id": "23456",
            "title": "Record 2",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "091", "subfields": [{"content": "Bar", "tag": "a"}]},
                {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "23456"
        assert response.cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    @pytest.mark.parametrize(
        "date, action",
        [("2025-01-01T01:00:00", "overlay"), ("2020-01-01T01:00:00", "attach")],
    )
    def test_resolve_no_call_no_match_vendor(self, cat_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": date,
            "varFields": [
                {"marcTag": "091", "subfields": [{"content": "Baz", "tag": "a"}]},
                {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert response.branch_call_number is not None
        assert result.call_number_match is False
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_no_call_no(self, cat_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": "2025-01-01T01:00:00",
            "varFields": [
                {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.branch_call_number is None
        assert result.call_number_match is False
        assert result.action == "overlay"


class TestNYPLCatResearchMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_resolve(self, sierra_response, cat_bib):
        reviewer = review.NYPLCatResearchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[sierra_response])
        assert cat_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_resolve_no_results(self, cat_bib):
        reviewer = review.NYPLCatResearchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[])
        assert cat_bib.bib_id is None
        assert result.target_bib_id is None

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    @pytest.mark.parametrize(
        "date, action",
        [("2025-01-01T01:00:00", "overlay"), ("2020-01-01T01:00:00", "attach")],
    )
    def test_resolve_vendor_record(self, cat_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": date,
            "varFields": [
                {
                    "marcTag": "852",
                    "ind1": "8",
                    "ind2": " ",
                    "subfields": [{"content": "Bar", "tag": "a"}],
                },
                {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatResearchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert len(response.research_call_number) > 0
        assert result.call_number_match is True
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_resolve_no_call_no(self, cat_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatResearchMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.research_call_number == []
        assert result.call_number_match is False
        assert result.action == "overlay"


class TestBPLCatMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve(self, sierra_response, cat_bib):
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[sierra_response])
        assert cat_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_results(self, cat_bib):
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[])
        assert cat_bib.bib_id is None
        assert result.target_bib_id is None

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_results_midwest(self, make_domain_bib):
        domain_bib = make_domain_bib(
            {
                "037": {"code": "b", "value": "Midwest"},
                "099": {"code": "a", "value": "DVD"},
            },
            "cat",
        )
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(domain_bib, candidates=[])
        assert domain_bib.bib_id is None
        assert result.target_bib_id is None

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_resolve_vendor_record(self, cat_bib, date, action):
        data = {
            "id": "12345",
            "title": "Record 2",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "12345"
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_call_no_match_inhouse(self, cat_bib):
        data = {
            "id": "23456",
            "title": "Record 2",
            "ss_marc_tag_005": "20200101010000.0",
            "ss_marc_tag_001": "ocn123456789",
            "ss_marc_tag_003": "OCoLC",
            "call_number": "Bar",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "23456"
        assert response.cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_resolve_no_call_no_match_vendor(self, cat_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Baz",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_call_no(self, cat_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": "20250101010000.0",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(cat_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert result.action == "overlay"
