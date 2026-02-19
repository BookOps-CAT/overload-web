import pytest

from overload_web.domain.models import sierra_responses


@pytest.fixture
def nypl_data():
    return {
        "id": "12345",
        "title": "Record 1",
        "updatedDate": "2000-01-01T01:00:00",
        "varFields": [],
    }


class TestCandidateClassifier:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_classify_matches_duplicates(self, full_bib, sierra_response):
        classified = full_bib.classify_matches([sierra_response, sierra_response])
        assert classified.duplicates == ["12345", "12345"]

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_matches_nypl_mixed(self, full_bib, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
        ]
        classified = full_bib.classify_matches([nypl_data])
        assert len(classified.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_matches_nypl_mixed_call_number(self, full_bib, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Foo", "tag": "a"}]},
            {
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"content": "Foo", "tag": "a"}],
            },
        ]
        classified = full_bib.classify_matches([nypl_data])
        assert len(classified.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_classify_matches_nypl_no_collection(self, full_bib, nypl_data):
        classified = full_bib.classify_matches([nypl_data])
        assert len(classified.mixed) == 0
        assert len(classified.duplicates) == 0
        assert len(classified.matched) == 0
        assert len(classified.other) == 1

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_classify_matches_unknown_library(self, full_bib, sierra_response):
        full_bib.library = "FOO"
        with pytest.raises(ValueError) as exc:
            full_bib.classify_matches([sierra_response])
        assert str(exc.value) == "Unknown library: FOO. Cannot classify matches."

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analysis_attr(self, acq_bib):
        with pytest.raises(AttributeError) as exc:
            acq_bib.analysis
        assert str(exc.value) == "MatchAnalysis has not been assigned to the DomainBib"


class TestSelectionMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze(self, sel_bib, sierra_response, caplog):
        result = sel_bib.analyze_matches(candidates=[sierra_response])
        assert "Analyzing matches with SelectionMatchAnalyzer" in caplog.text
        assert sel_bib.bib_id is None
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
        assert result.target_title == "Record 1"

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_analyze_no_matches(self, sel_bib, caplog):
        result = sel_bib.analyze_matches(candidates=[])
        assert "Analyzing matches with SelectionMatchAnalyzer" in caplog.text
        assert sel_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_analyze_no_call_no(self, sel_bib, collection, nypl_data, caplog):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]}
        ]
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        result = sel_bib.analyze_matches(candidates=[nypl_data])
        assert "Analyzing matches with SelectionMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert sel_bib.bib_id is None
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 1"
        assert response.branch_call_number is None
        assert response.research_call_number == []


@pytest.mark.parametrize(
    "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
)
class TestAcquisitionsMatchAnalyzer:
    def test_analyze(self, acq_bib, sierra_response, caplog):
        result = acq_bib.analyze_matches(candidates=[sierra_response])
        assert "Analyzing matches with AcquisitionsMatchAnalyzer" in caplog.text
        assert acq_bib.bib_id is None
        assert result.target_bib_id == acq_bib.bib_id
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == result.call_number
        assert result.target_title == acq_bib.title

    @pytest.mark.parametrize(
        "key, value",
        [
            ("control_number", "123456789"),
            ("isbn", "123456789"),
            ("oclc_number", "123456789"),
            ("oclc_number", ["123456789", "987654321"]),
            ("upc", "123456789"),
        ],
    )
    def test_resource_id(self, acq_bib, sierra_response, key, value):
        acq_bib.isbn = None
        setattr(acq_bib, key, value)
        results = acq_bib.analyze_matches(candidates=[sierra_response])
        assert results.resource_id == "123456789"
        assert results.call_number == "Foo"

    def test_resource_id_none(self, acq_bib, sierra_response):
        acq_bib.isbn = None
        results = acq_bib.analyze_matches(candidates=[sierra_response])
        assert results.resource_id is None
        assert acq_bib.control_number is None
        assert acq_bib.isbn is None
        assert acq_bib.oclc_number is None
        assert acq_bib.upc is None


@pytest.mark.parametrize("library, collection", [("nypl", "BL")])
class TestNYPLCatBranchMatchAnalyzer:
    def test_analyze(self, full_bib, sierra_response, caplog):
        result = full_bib.analyze_matches(candidates=[sierra_response])
        assert "Analyzing matches with NYPLCatBranchMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
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
        assert result.target_title == "Record 1"

    def test_analyze_no_matches(self, full_bib, caplog):
        result = full_bib.analyze_matches(candidates=[])
        assert "Analyzing matches with NYPLCatBranchMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title is None

    def test_analyze_no_call_number_match_inhouse_source(
        self, full_bib, nypl_data, caplog
    ):
        nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Bar", "tag": "a"}]},
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
        ]
        response = sierra_responses.NYPLPlatformResponse(nypl_data)
        result = full_bib.analyze_matches(candidates=[nypl_data])
        assert "Analyzing matches with NYPLCatBranchMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "12345"
        assert response.cat_source == "inhouse"
        assert result.action == "attach"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Bar"
        assert result.target_title == "Record 1"

    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "overlay", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    def test_analyze_no_call_number_match_vendor_source(
        self, full_bib, date, action, updated, nypl_data, caplog
    ):
        nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Baz", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
        ]
        nypl_data["updatedDate"] = date
        response = sierra_responses.NYPLPlatformResponse(nypl_data)
        result = full_bib.analyze_matches(candidates=[nypl_data])
        assert "Analyzing matches with NYPLCatBranchMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "12345"
        assert response.cat_source == "vendor"
        assert response.branch_call_number is not None
        assert result.action == action
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.resource_id == "9781234567890"
        assert result.mixed == []
        assert result.other == []
        assert result.call_number_match is False
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Baz"
        assert result.target_title == "Record 1"
        # test that NYPLPlatformResponse is parsing data correctly
        assert response.barcodes == []
        assert response.control_number is None
        assert response.isbn == []
        assert response.oclc_number == []
        assert response.upc == []


@pytest.mark.parametrize("library, collection", [("nypl", "RL")])
class TestNYPLCatResearchMatchAnalyzer:
    def test_analyze(self, full_bib, sierra_response, caplog):
        result = full_bib.analyze_matches(candidates=[sierra_response])
        assert "Analyzing matches with NYPLCatResearchMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == "Foo"
        assert result.target_bib_id == "12345"
        assert result.target_title == "Record 1"

    def test_analyze_no_results(self, full_bib, caplog):
        result = full_bib.analyze_matches(candidates=[])
        assert "Analyzing matches with NYPLCatResearchMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
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
    def test_analyze_vendor_record(
        self, full_bib, date, action, updated, nypl_data, caplog
    ):
        nypl_data["varFields"] = [
            {
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"content": "Bar", "tag": "a"}],
            },
        ]
        nypl_data["updatedDate"] = date
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        result = full_bib.analyze_matches(candidates=[nypl_data])
        assert "Analyzing matches with NYPLCatResearchMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert response.cat_source == "vendor"
        assert result.action == action
        assert result.mixed == []
        assert result.other == []
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.call_number_match is True
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Bar"
        assert result.target_title == "Record 1"

    def test_analyze_no_call_no(self, full_bib, nypl_data, caplog):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        ]
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        result = full_bib.analyze_matches(candidates=[nypl_data])
        assert "Analyzing matches with NYPLCatResearchMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert response.research_call_number == []
        assert result.call_number_match is False
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.mixed == []
        assert result.other == []
        assert result.action == "overlay"
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 1"


@pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
class TestBPLCatMatchAnalyzer:
    def test_analyze(self, full_bib, sierra_response, caplog):
        result = full_bib.analyze_matches(candidates=[sierra_response])
        response = sierra_responses.BPLSolrResponse(data=sierra_response)
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        # test that the BPL response is parsed correctly
        assert response.barcodes == ["33333123456789"]
        assert response.control_number == "ocn123456789"
        assert response.isbn == ["9781234567890"]
        assert sorted(response.oclc_number) == sorted(["ocn123456789"])
        assert response.research_call_number == []
        assert sorted(response.upc) == sorted(["12345"])

    def test_analyze_no_results(self, full_bib, caplog):
        result = full_bib.analyze_matches(candidates=[])
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "insert"

    def test_analyze_no_results_midwest(self, full_bib, caplog):
        full_bib.vendor = "Midwest DVD"
        result = full_bib.analyze_matches(candidates=[])
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "attach"

    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_analyze_vendor_record(self, full_bib, date, action, caplog):
        data = {
            "id": "12345",
            "title": "Record 2",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        result = full_bib.analyze_matches(candidates=[data])
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "12345"
        assert result.action == action

    def test_analyze_no_call_no_match_inhouse(self, full_bib, caplog):
        data = {
            "id": "23456",
            "title": "Record 2",
            "ss_marc_tag_005": "20200101010000.0",
            "ss_marc_tag_001": "ocn123456789",
            "ss_marc_tag_003": "OCoLC",
            "call_number": "Bar",
        }
        response = sierra_responses.BPLSolrResponse(data=data)
        result = full_bib.analyze_matches(candidates=[data])
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "23456"
        assert response.cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_analyze_no_call_no_match_vendor(self, full_bib, date, action, caplog):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Baz",
        }
        response = sierra_responses.BPLSolrResponse(data=data)
        result = full_bib.analyze_matches(candidates=[data])
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert result.action == action

    def test_analyze_no_call_no(self, full_bib, caplog):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": "20250101010000.0",
        }
        result = full_bib.analyze_matches(candidates=[data])
        assert "Analyzing matches with BPLCatMatchAnalyzer" in caplog.text
        assert result.target_bib_id == "34567"
        assert result.action == "overlay"
