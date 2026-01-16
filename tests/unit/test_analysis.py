import pytest

from overload_web.bib_records.domain_models import sierra_responses
from overload_web.bib_records.domain_services import analysis


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


@pytest.fixture
def full_record_response(full_bib, sierra_response):
    return sierra_responses.MatchContext(bib=full_bib, candidates=[sierra_response])


@pytest.fixture
def order_record_response(order_level_bib, sierra_response, collection):
    order_level_bib.collection = collection
    return sierra_responses.MatchContext(
        bib=order_level_bib, candidates=[sierra_response]
    )


class TestMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_base_analyzer(self, order_record_response):
        service = analysis.BaseMatchAnalyzer()
        with pytest.raises(NotImplementedError):
            service.analyze(order_record_response)

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze_matches(self, order_record_response):
        service = analysis.AcquisitionsMatchAnalyzer()
        attached_bibs = service.analyze_matches([order_record_response])
        assert attached_bibs[0].target_bib_id is None
        assert order_record_response.bib.bib_id is None


class TestCandidateClassifier:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_classify(self, full_record_response):
        full_record_response.candidates.append(full_record_response.candidates[0])
        classified = full_record_response.classify()
        assert classified.duplicates == ["12345", "12345"]

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_classify_no_candidates(self, full_record_response):
        full_record_response.candidates = []
        classified = full_record_response.classify()
        assert classified.duplicates == []

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_nypl_mixed(self, full_record_response, nypl_data):
        nypl_data["varFields"].extend(
            [
                {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
                {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
            ]
        )
        full_record_response.candidates = [
            sierra_responses.NYPLPlatformResponse(data=nypl_data)
        ]
        classified = full_record_response.classify()
        assert len(classified.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_nypl_unmatched(self, full_record_response):
        full_record_response.bib.collection = "NONE"
        classified = full_record_response.classify()
        assert len(classified.other) == 1
        assert len(classified.matched) == 0

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    @pytest.mark.parametrize(
        "key",
        ["control_number", "isbn", "oclc_number", "upc"],
    )
    def test_resource_id(self, full_bib, sierra_response, key):
        full_bib.isbn = None
        setattr(full_bib, key, "123456789")
        response = sierra_responses.MatchContext(
            bib=full_bib, candidates=[sierra_response]
        )
        assert response.resource_id == "123456789"
        assert response.input_call_no == "Foo"

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_resource_id_multiple_oclc_numbers(self, full_bib, sierra_response):
        full_bib.isbn = None
        full_bib.oclc_number = ["123456789", "987654321"]
        response = sierra_responses.MatchContext(
            bib=full_bib, candidates=[sierra_response]
        )
        assert response.resource_id == "123456789"

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_resource_id_none(self, full_bib, sierra_response):
        full_bib.isbn = None
        response = sierra_responses.MatchContext(
            bib=full_bib, candidates=[sierra_response]
        )
        assert response.resource_id is None
        assert response.bib.control_number is None
        assert response.bib.isbn is None
        assert response.bib.oclc_number is None
        assert response.bib.upc is None


class TestSelectionMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze(self, order_record_response):
        order_record_response.bib.record_type = "sel"
        analyzer = analysis.SelectionMatchAnalyzer()
        result = analyzer.analyze(order_record_response)
        assert order_record_response.bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.domain_bib is not None
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
    def test_analyze_no_matches(self, order_record_response):
        order_record_response.bib.record_type = "sel"
        order_record_response.candidates = []
        analyzer = analysis.SelectionMatchAnalyzer()
        result = analyzer.analyze(order_record_response)
        assert order_record_response.bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.domain_bib is not None
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
    def test_analyze_no_call_no(self, order_record_response, collection, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]}
        ]
        order_record_response.candidates = [
            sierra_responses.NYPLPlatformResponse(data=nypl_data)
        ]
        analyzer = analysis.SelectionMatchAnalyzer()
        result = analyzer.analyze(order_record_response)
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert order_record_response.bib.bib_id is None
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "BTSERIES"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 1"
        assert order_record_response.candidates[0].branch_call_number is None
        assert order_record_response.candidates[0].research_call_number == []


class TestAcquisitionsMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze(self, order_record_response):
        order_record_response.bib.record_type = "acq"
        analyzer = analysis.AcquisitionsMatchAnalyzer()
        result = analyzer.analyze(order_record_response)
        assert order_record_response.bib.bib_id is None
        assert result.target_bib_id == order_record_response.bib.bib_id
        assert result.duplicate_records == []
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "BTSERIES"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == result.input_call_no
        assert result.target_title == order_record_response.bib.title


class TestNYPLCatBranchMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_analyze(self, full_record_response):
        analyzer = analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_title == "Record 1"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_analyze_no_matches(self, full_record_response):
        full_record_response.candidates = []
        analyzer = analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_analyze_no_call_number_match_inhouse_source(self, full_record_response):
        data = {
            "id": "23456",
            "title": "Record 2",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "091", "subfields": [{"content": "Bar", "tag": "a"}]},
                {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            ],
        }
        full_record_response.candidates = [sierra_responses.NYPLPlatformResponse(data)]
        analyzer = analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert result.target_bib_id == "23456"
        assert full_record_response.candidates[0].cat_source == "inhouse"
        assert result.action == "attach"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Bar"
        assert result.target_title == "Record 2"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "overlay", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    def test_analyze_no_call_number_match_vendor_source(
        self, full_record_response, date, action, updated
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
        full_record_response.candidates = [sierra_responses.NYPLPlatformResponse(data)]
        analyzer = analysis.NYPLCatBranchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert result.target_bib_id == "34567"
        assert full_record_response.candidates[0].cat_source == "vendor"
        assert full_record_response.candidates[0].branch_call_number is not None
        assert result.action == action
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.call_number_match is False
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Baz"
        assert result.target_title == "Record 3"


class TestNYPLCatResearchMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_analyze(self, full_record_response):
        analyzer = analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.input_call_no == "Foo"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_bib_id == "12345"
        assert result.target_title == "Record 1"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_analyze_no_results(self, full_record_response):
        full_record_response.candidates = []
        analyzer = analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.input_call_no == "Foo"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_bib_id is None
        assert result.target_title is None

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "overlay", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    def test_analyze_vendor_record(self, full_record_response, date, action, updated):
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
        full_record_response.candidates = [sierra_responses.NYPLPlatformResponse(data)]
        analyzer = analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id == "34567"
        assert full_record_response.candidates[0].cat_source == "vendor"
        assert result.action == action
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.duplicate_records == []
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.input_call_no == "Foo"
        assert result.call_number_match is True
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Bar"
        assert result.target_title == "Record 3"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_analyze_no_call_no(self, full_record_response):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
            ],
        }
        full_record_response.candidates = [sierra_responses.NYPLPlatformResponse(data)]
        analyzer = analysis.NYPLCatResearchMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id == "34567"
        assert full_record_response.candidates[0].research_call_number == []
        assert result.call_number_match is False
        assert result.duplicate_records == []
        assert result.domain_bib is not None
        assert result.resource_id == "9781234567890"
        assert result.input_call_no == "Foo"
        assert result.vendor == "UNKNOWN"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "overlay"
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 3"


class TestBPLCatMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_analyze(self, full_record_response):
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_analyze_no_results(self, full_record_response):
        full_record_response.candidates = []
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == sierra_responses.CatalogAction.INSERT

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_analyze_no_results_midwest(self, full_record_response):
        full_record_response.bib.vendor = "Midwest DVD"
        full_record_response.candidates = []
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert full_record_response.bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "attach"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_analyze_vendor_record(self, full_record_response, date, action):
        data = {
            "id": "12345",
            "title": "Record 2",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        full_record_response.candidates = [sierra_responses.BPLSolrResponse(data)]
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert result.target_bib_id == "12345"
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_analyze_no_call_no_match_inhouse(self, full_record_response):
        data = {
            "id": "23456",
            "title": "Record 2",
            "ss_marc_tag_005": "20200101010000.0",
            "ss_marc_tag_001": "ocn123456789",
            "ss_marc_tag_003": "OCoLC",
            "call_number": "Bar",
        }
        full_record_response.candidates = [sierra_responses.BPLSolrResponse(data)]
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert result.target_bib_id == "23456"
        assert full_record_response.candidates[0].cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_analyze_no_call_no_match_vendor(self, full_record_response, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Baz",
        }
        full_record_response.candidates = [sierra_responses.BPLSolrResponse(data)]
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert result.target_bib_id == "34567"
        assert full_record_response.candidates[0].cat_source == "vendor"
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_analyze_no_call_no(self, full_record_response):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": "20250101010000.0",
        }
        full_record_response.candidates = [sierra_responses.BPLSolrResponse(data)]
        analyzer = analysis.BPLCatMatchAnalyzer()
        result = analyzer.analyze(full_record_response)
        assert result.target_bib_id == "34567"
        assert result.action == "overlay"
