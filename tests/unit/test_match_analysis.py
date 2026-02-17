import pytest

from overload_web.domain.models import bibs, sierra_responses
from overload_web.domain.services import match_analysis


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


@pytest.mark.parametrize(
    "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
)
class TestMatchAnalyzer:
    def test_analyze(self, acq_bib, sierra_response):
        service = match_analysis.AcquisitionsMatchAnalyzer()
        results = service.analyze(record=acq_bib, candidates=[sierra_response])
        assert results.decision.target_bib_id is None
        assert acq_bib.bib_id is None

    @pytest.mark.parametrize("key", ["control_number", "isbn", "oclc_number", "upc"])
    def test_resource_id(self, full_bib, sierra_response, key):
        full_bib.isbn = None
        setattr(full_bib, key, "123456789")
        service = match_analysis.AcquisitionsMatchAnalyzer()
        results = service.analyze(record=full_bib, candidates=[sierra_response])
        assert results.resource_id == "123456789"
        assert results.call_number == "Foo"

    def test_resource_id_multiple_oclc_numbers(self, full_bib, sierra_response):
        full_bib.isbn = None
        full_bib.oclc_number = ["123456789", "987654321"]
        service = match_analysis.AcquisitionsMatchAnalyzer()
        results = service.analyze(record=full_bib, candidates=[sierra_response])
        assert results.resource_id == "123456789"
        assert results.call_number == "Foo"

    def test_resource_id_none(self, full_bib, sierra_response):
        full_bib.isbn = None
        service = match_analysis.AcquisitionsMatchAnalyzer()
        results = service.analyze(record=full_bib, candidates=[sierra_response])
        assert results.resource_id is None
        assert full_bib.control_number is None
        assert full_bib.isbn is None
        assert full_bib.oclc_number is None
        assert full_bib.upc is None


class TestCandidateClassifier:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_classify_matches(self, full_bib, sierra_response):
        classified = full_bib.classify_matches([sierra_response, sierra_response])
        assert classified.duplicates == ["12345", "12345"]

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_classify_matches_no_candidates(self, full_bib):
        classified = full_bib.classify_matches([])
        assert classified.duplicates == []

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_matches_nypl_mixed(self, full_bib, nypl_data):
        classified = full_bib.classify_matches(
            [sierra_responses.NYPLPlatformResponse(data=nypl_data)]
        )
        assert len(classified.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_matches_nypl_unmatched(self, full_bib, sierra_response):
        full_bib.collection = "NONE"
        classified = full_bib.classify_matches([sierra_response])
        assert len(classified.other) == 1
        assert len(classified.matched) == 0


class TestSelectionMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze(self, sel_bib, sierra_response):
        analyzer = match_analysis.SelectionMatchAnalyzer()
        result = analyzer.analyze(record=sel_bib, candidates=[sierra_response])
        assert sel_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.vendor == "BTSERIES"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_title == "Record 1"

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze_no_matches(self, sel_bib):
        analyzer = match_analysis.SelectionMatchAnalyzer()
        result = analyzer.analyze(record=sel_bib, candidates=[])
        assert sel_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.vendor == "BTSERIES"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_analyze_no_call_no(self, sel_bib, collection, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]}
        ]
        candidates = [sierra_responses.NYPLPlatformResponse(data=nypl_data)]
        analyzer = match_analysis.SelectionMatchAnalyzer()
        result = analyzer.analyze(sel_bib, candidates=candidates)
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert sel_bib.bib_id is None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "BTSERIES"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 1"
        assert candidates[0].branch_call_number is None
        assert candidates[0].research_call_number == []


class TestAcquisitionsMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze(self, acq_bib, sierra_response):
        analyzer = match_analysis.AcquisitionsMatchAnalyzer()
        result = analyzer.analyze(record=acq_bib, candidates=[sierra_response])
        assert acq_bib.bib_id is None
        assert result.target_bib_id == acq_bib.bib_id
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.vendor == "BTSERIES"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == result.call_number
        assert result.target_title == acq_bib.title


@pytest.mark.parametrize("library, collection", [("nypl", "BL")])
class TestNYPLCatBranchMatchAnalyzer:
    def test_analyze(self, full_bib, sierra_response):
        analyzer = match_analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[sierra_response])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_title == "Record 1"

    def test_analyze_no_matches(self, full_bib):
        analyzer = match_analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[])
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title is None

    def test_analyze_no_call_number_match_inhouse_source(self, full_bib):
        data = {
            "id": "23456",
            "title": "Record 2",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "091", "subfields": [{"content": "Bar", "tag": "a"}]},
                {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            ],
        }
        candidates = [sierra_responses.NYPLPlatformResponse(data)]
        analyzer = match_analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=candidates)
        assert result.target_bib_id == "23456"
        assert candidates[0].cat_source == "inhouse"
        assert result.action == "attach"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Bar"
        assert result.target_title == "Record 2"

    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "overlay", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    def test_analyze_no_call_number_match_vendor_source(
        self, full_bib, date, action, updated
    ):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": date,
            "varFields": [
                {"marcTag": "091", "subfields": [{"content": "Baz", "tag": "a"}]},
                {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            ],
        }
        candidates = [sierra_responses.NYPLPlatformResponse(data)]
        analyzer = match_analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=candidates)
        assert result.target_bib_id == "34567"
        assert candidates[0].cat_source == "vendor"
        assert candidates[0].branch_call_number is not None
        assert result.action == action
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.call_number_match is False
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Baz"
        assert result.target_title == "Record 3"


@pytest.mark.parametrize("library, collection", [("nypl", "RL")])
class TestNYPLCatResearchMatchAnalyzer:
    def test_analyze(self, full_bib, sierra_response):
        analyzer = match_analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[sierra_response])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_bib_id == "12345"
        assert result.target_title == "Record 1"

    def test_analyze_no_results(self, full_bib):
        analyzer = match_analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[])
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_bib_id is None
        assert result.target_title is None

    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "overlay", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    def test_analyze_vendor_record(self, full_bib, date, action, updated):
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
        candidates = [sierra_responses.NYPLPlatformResponse(data=data)]
        analyzer = match_analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(
            record=full_bib,
            candidates=candidates,
        )
        assert full_bib.bib_id is None
        assert result.target_bib_id == "34567"
        assert candidates[0].cat_source == "vendor"
        assert result.action == action
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.call_number_match is True
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Bar"
        assert result.target_title == "Record 3"

    def test_analyze_no_call_no(self, full_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
            ],
        }
        candidates = [sierra_responses.NYPLPlatformResponse(data=data)]
        analyzer = match_analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=candidates)
        assert full_bib.bib_id is None
        assert result.target_bib_id == "34567"
        assert candidates[0].research_call_number == []
        assert result.call_number_match is False
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "overlay"
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 3"


@pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
class TestBPLCatMatchAnalyzer:
    def test_analyze(self, full_bib, sierra_response):
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[sierra_response])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"

    def test_analyze_no_results(self, full_bib):
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[])
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == bibs.CatalogAction.INSERT

    def test_analyze_no_results_midwest(self, full_bib):
        full_bib.vendor = "Midwest DVD"
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=[])
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "attach"

    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_analyze_vendor_record(self, full_bib, date, action):
        data = {
            "id": "12345",
            "title": "Record 2",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(
            record=full_bib, candidates=[sierra_responses.BPLSolrResponse(data=data)]
        )
        assert result.target_bib_id == "12345"
        assert result.action == action

    def test_analyze_no_call_no_match_inhouse(self, full_bib):
        data = {
            "id": "23456",
            "title": "Record 2",
            "ss_marc_tag_005": "20200101010000.0",
            "ss_marc_tag_001": "ocn123456789",
            "ss_marc_tag_003": "OCoLC",
            "call_number": "Bar",
        }
        candidates = [sierra_responses.BPLSolrResponse(data=data)]
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=candidates)
        assert result.target_bib_id == "23456"
        assert candidates[0].cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_analyze_no_call_no_match_vendor(self, full_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Baz",
        }
        candidates = [sierra_responses.BPLSolrResponse(data=data)]
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(record=full_bib, candidates=candidates)
        assert result.target_bib_id == "34567"
        assert candidates[0].cat_source == "vendor"
        assert result.action == action

    def test_analyze_no_call_no(self, full_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": "20250101010000.0",
        }
        analyzer = match_analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(
            record=full_bib, candidates=[sierra_responses.BPLSolrResponse(data=data)]
        )
        assert result.target_bib_id == "34567"
        assert result.action == "overlay"
