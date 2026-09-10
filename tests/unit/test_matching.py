import copy

import pytest

from overload_web.domain.pvf import matching, models
from overload_web.domain.shared import sierra_responses


@pytest.fixture(params=["BL", "RL"])
def stub_nypl_bib(request):
    return models.DomainBib(
        library="nypl",
        collection=request.param,
        isbn="9781234567890",
        title="Foo",
        record_type="cat",
        binary_data=b"",
        parsed_fields=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN", matchpoints={"primary_matchpoint": "isbn"}, bib_fields=[]
        ),
    )


@pytest.fixture
def nypl_bl_bib():
    return models.DomainBib(
        library="nypl",
        collection="BL",
        isbn="9781234567890",
        title="Foo",
        record_type="cat",
        binary_data=b"",
        parsed_fields=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN", matchpoints={"primary_matchpoint": "isbn"}, bib_fields=[]
        ),
    )


@pytest.fixture
def nypl_rl_bib():
    return models.DomainBib(
        library="nypl",
        collection="RL",
        isbn="9781234567890",
        title="Foo",
        record_type="cat",
        binary_data=b"",
        parsed_fields=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN", matchpoints={"primary_matchpoint": "isbn"}, bib_fields=[]
        ),
    )


@pytest.fixture
def bpl_bib():
    return models.DomainBib(
        library="bpl",
        collection=None,
        isbn="9781234567890",
        title="Foo",
        record_type="cat",
        binary_data=b"",
        parsed_fields=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN", matchpoints={"primary_matchpoint": "isbn"}, bib_fields=[]
        ),
    )


@pytest.fixture
def stub_nypl_data():
    return {
        "id": "12345",
        "title": "Record 1",
        "updatedDate": "2020-01-01T00:00:01",
        "varFields": [],
        "locations": [
            {"code": "a", "name": "library"},
            {"code": "123", "name": "library"},
        ],
    }


@pytest.fixture
def nypl_bl_data(stub_nypl_data):
    data = copy.deepcopy(stub_nypl_data)
    data["varFields"].extend(
        [
            {
                "marcTag": "091",
                "ind1": " ",
                "ind2": " ",
                "subfields": [{"content": "Foo", "tag": "a"}],
            },
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
        ]
    )
    return data


@pytest.fixture
def nypl_rl_data(stub_nypl_data):
    data = copy.deepcopy(stub_nypl_data)
    data["varFields"].extend(
        [
            {
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"content": "Foo", "tag": "a"}],
            },
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
        ]
    )
    return data


@pytest.fixture
def bpl_data():
    return {
        "call_number": "Foo",
        "id": "12345",
        "isbn": ["9781234567890"],
        "sm_bib_varfields": ["005 || 20200101000001.0", "024 || {{a}} 12345"],
        "sm_item_data": ['{"barcode": "33333123456789"}'],
        "ss_marc_tag_001": "ocn123456789",
        "ss_marc_tag_003": "OCoLC",
        "ss_marc_tag_005": "20200101000001.0",
        "title": "Record 1",
    }


class TestClassifyMatches:
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_classify_matches_bpl(self, bpl_bib, bpl_data, record_type):
        matcher = matching.MatchAnalyzerFactory.make("bpl", record_type, None)
        classified = matcher.classify_matches(bpl_bib, matches=[bpl_data, bpl_data])
        assert len(classified.matched) == 2
        assert len(classified.mixed) == 0
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 2

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_classify_matches_nypl_bl(self, nypl_bl_bib, nypl_bl_data, record_type):
        matcher = matching.MatchAnalyzerFactory.make("nypl", record_type, "BL")
        classified = matcher.classify_matches(
            nypl_bl_bib, matches=[nypl_bl_data, nypl_bl_data]
        )
        assert len(classified.matched) == 2
        assert len(classified.mixed) == 0
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 2

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_classify_matches_nypl_rl(self, nypl_rl_bib, nypl_rl_data, record_type):
        matcher = matching.MatchAnalyzerFactory.make("nypl", record_type, "RL")
        classified = matcher.classify_matches(
            nypl_rl_bib, matches=[nypl_rl_data, nypl_rl_data]
        )
        assert len(classified.matched) == 2
        assert len(classified.mixed) == 0
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 2

    @pytest.mark.parametrize("collection", ["BL", "RL"])
    def test_classify_matches_nypl_mixed_910s(
        self, stub_nypl_bib, stub_nypl_data, collection
    ):
        stub_nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
        ]
        matcher = matching.MatchAnalyzerFactory.make("nypl", "cat", collection)
        classified = matcher.classify_matches(stub_nypl_bib, matches=[stub_nypl_data])
        assert len(classified.matched) == 0
        assert len(classified.mixed) == 1
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 0

    @pytest.mark.parametrize("collection", ["BL", "RL"])
    def test_classify_matches_nypl_mixed_call_numbers(
        self, stub_nypl_bib, stub_nypl_data, collection
    ):
        call_no = [{"content": "Foo", "tag": "a"}]
        stub_nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": call_no},
            {"marcTag": "852", "ind1": "8", "ind2": " ", "subfields": call_no},
        ]
        matcher = matching.MatchAnalyzerFactory.make("nypl", "cat", collection)
        classified = matcher.classify_matches(stub_nypl_bib, matches=[stub_nypl_data])
        assert len(classified.matched) == 0
        assert len(classified.mixed) == 1
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 0

    @pytest.mark.parametrize("collection", ["BL", "RL"])
    def test_classify_matches_nypl_no_collection(
        self, stub_nypl_bib, stub_nypl_data, collection
    ):
        matcher = matching.MatchAnalyzerFactory.make("nypl", "cat", collection)
        classified = matcher.classify_matches(stub_nypl_bib, matches=[stub_nypl_data])
        assert len(classified.matched) == 0
        assert len(classified.mixed) == 0
        assert len(classified.other) == 1
        assert len(classified.duplicates) == 0

    @pytest.mark.parametrize("location", ["zzzzz", "myj", "maj", "agj"])
    def test_classify_matches_nypl_bl_locations(
        self, nypl_bl_bib, stub_nypl_data, location
    ):
        stub_nypl_data["locations"] = [{"code": location, "name": "Foo"}]
        matcher = matching.MatchAnalyzerFactory.make("nypl", "cat", "BL")
        classified = matcher.classify_matches(nypl_bl_bib, matches=[stub_nypl_data])
        assert len(classified.matched) == 1
        assert len(classified.mixed) == 0
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 0

    @pytest.mark.parametrize("location", ["myd", "xxx", "lsx", "scx", "max"])
    def test_classify_matches_nypl_rl_locations(
        self, nypl_rl_bib, stub_nypl_data, location
    ):
        stub_nypl_data["locations"] = [{"code": location, "name": "Foo"}]
        matcher = matching.MatchAnalyzerFactory.make("nypl", "cat", "RL")
        classified = matcher.classify_matches(nypl_rl_bib, matches=[stub_nypl_data])
        assert len(classified.matched) == 1
        assert len(classified.mixed) == 0
        assert len(classified.other) == 0
        assert len(classified.duplicates) == 0


class TestDetermineCatalogAction:
    def test_determine_catalog_action_bpl(self, bpl_bib, bpl_data):
        matcher = matching.SelectionMatchAnalyzer()
        bpl_data = {k: v for k, v in bpl_data.items() if k != "ss_marc_tag_005"}
        response = sierra_responses.BPLSolrResponse(bpl_data)
        action, updated = matcher.determine_catalog_action(bpl_bib, candidate=response)
        assert action == "attach"
        assert updated is False
        assert response.barcodes == ["33333123456789"]
        assert response.branch_call_number == "Foo"
        assert response.cat_source == "inhouse"
        assert response.collection == "NONE"
        assert response.control_number == "ocn123456789"
        assert response.isbn == ["9781234567890"]
        assert response.oclc_number == ["ocn123456789"]
        assert response.research_call_number == []
        assert response.upc == ["12345"]
        assert response.update_date is None
        assert response.update_datetime is None
        assert response.var_fields == [
            {"marc_tag": "024", "subfields": [{"tag": "a", "content": "12345"}]}
        ]

    def test_determine_catalog_action_nypl(self, nypl_bl_bib, nypl_bl_data):
        matcher = matching.SelectionMatchAnalyzer()
        nypl_bl_data = {k: v for k, v in nypl_bl_data.items() if k != "updatedDate"}
        response = sierra_responses.NYPLPlatformResponse(nypl_bl_data)
        action, updated = matcher.determine_catalog_action(
            nypl_bl_bib, candidate=response
        )
        assert action == "attach"
        assert updated is False
        assert response.barcodes == []
        assert response.branch_call_number == "Foo"
        assert response.cat_source == "inhouse"
        assert response.control_number is None
        assert response.isbn == []
        assert response.oclc_number == []
        assert response.research_call_number == []
        assert response.upc == []
        assert response.update_date is None
        assert response.update_datetime is None
        assert len(response.var_fields) == 3

    def test_determine_catalog_action_update(self, stub_nypl_data, nypl_bl_bib):
        matcher = matching.SelectionMatchAnalyzer()
        response = sierra_responses.NYPLPlatformResponse(stub_nypl_data)
        action, updated = matcher.determine_catalog_action(
            nypl_bl_bib, candidate=response
        )
        assert action == "update"
        assert updated is True
        assert response.cat_source == "vendor"

    def test_determine_catalog_action_vendor_record_nypl(
        self, stub_nypl_data, nypl_bl_bib
    ):
        matcher = matching.SelectionMatchAnalyzer()
        nypl_bl_bib.update_date = "20250101000001.0"
        response = sierra_responses.NYPLPlatformResponse(stub_nypl_data)
        action, updated = matcher.determine_catalog_action(
            nypl_bl_bib, candidate=response
        )
        assert action == "attach"
        assert updated is False
        assert response.cat_source == "vendor"

    def test_determine_catalog_action_vendor_record_bpl(self, bpl_data, bpl_bib):
        matcher = matching.SelectionMatchAnalyzer()
        bpl_bib.update_date = "20250101000001.0"
        bpl_data = {k: v for k, v in bpl_data.items() if k != "ss_marc_tag_003"}
        response = sierra_responses.BPLSolrResponse(bpl_data)
        action, updated = matcher.determine_catalog_action(bpl_bib, candidate=response)
        assert action == "attach"
        assert updated is False
        assert response.cat_source == "vendor"

    def test_catalog_action_unassigned_attr(self, nypl_bl_bib):
        with pytest.raises(AttributeError) as exc:
            nypl_bl_bib.action
        assert str(exc.value) == "CatalogAction has not been assigned to the DomainBib"


class TestAcquisitionsMatchAnalyzer:
    @pytest.mark.parametrize(
        "key, value, output",
        [
            ("control_number", "123456789", "123456789"),
            ("oclc_number", [], None),
            ("oclc_number", "123456789", "123456789"),
            ("oclc_number", ["123456789", "987654321"], "123456789"),
            ("upc", "123456789", "123456789"),
        ],
    )
    def test_analyze(self, stub_nypl_data, nypl_bl_bib, key, value, output):
        nypl_bl_bib.isbn = None
        nypl_bl_bib.record_type = "acq"
        setattr(nypl_bl_bib, key, value)
        matcher = matching.AcquisitionsMatchAnalyzer()
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(stub_nypl_data)], [], []
        )
        result = matcher.analyze(nypl_bl_bib, candidates=candidates)
        assert result.action == "insert"
        assert result.call_number == nypl_bl_bib.call_number
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert len(result.duplicate_records) == 0
        assert len(result.other) == 0
        assert len(result.mixed) == 0
        assert result.resource_id == output
        assert result.target_bib_id == nypl_bl_bib.bib_id
        assert result.target_call_no == nypl_bl_bib.branch_call_number
        assert result.target_title == nypl_bl_bib.title
        assert result.vendor == nypl_bl_bib.vendor


class TestBPLCatMatchAnalyzer:
    MATCHER = matching.BPLCatMatchAnalyzer()

    @pytest.mark.parametrize("call_number, match", [("Foo", True), ("Bar", False)])
    def test_analyze(self, bpl_bib, bpl_data, call_number, match):
        bpl_bib.branch_call_number = call_number
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.BPLSolrResponse(bpl_data)], [], []
        )
        result = self.MATCHER.analyze(bpl_bib, candidates=candidates)
        assert result.call_number_match == match

    def test_analyze_call_no(self, bpl_bib, bpl_data):
        bpl_bib.branch_call_number = "Foo"
        bpl_data["call_number"] = None
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.BPLSolrResponse(bpl_data)], [], []
        )
        result = self.MATCHER.analyze(bpl_bib, candidates=candidates)
        assert result.call_number_match is False

    @pytest.mark.parametrize(
        "vendor, action",
        [
            ("Midwest DVD", "attach"),
            ("Midwest Audio", "attach"),
            ("Midwest CD", "attach"),
            ("East View", "insert"),
        ],
    )
    def test_analyze_no_matches_by_vendor(self, bpl_bib, vendor, action):
        bpl_bib.vendor = vendor
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.MATCHER.analyze(bpl_bib, candidates=candidates)
        assert bpl_bib.bib_id is None
        assert result.target_bib_id == bpl_bib.bib_id
        assert result.action == action
        assert result.call_number == bpl_bib.call_number
        assert result.call_number_match is True
        assert result.target_call_no is None
        assert result.target_title is None


class TestNYPLCatResearchMatchAnalyzer:
    MATCHER = matching.NYPLCatResearchMatchAnalyzer()

    @pytest.mark.parametrize("call_number, match", [("Foo", True), ("Bar", True)])
    def test_analyze(self, nypl_rl_bib, nypl_rl_data, call_number, match):
        nypl_rl_bib.research_call_number = call_number
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(nypl_rl_data)], [], []
        )
        result = self.MATCHER.analyze(nypl_rl_bib, candidates=candidates)
        assert result.call_number_match == match
        assert result.target_call_no == "Foo"

    def test_analyze_no_response_call_no(self, nypl_rl_bib, nypl_rl_data):
        data = copy.deepcopy(nypl_rl_data)
        data["varFields"] = [i for i in data["varFields"] if i["marcTag"] != "852"]
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(data)], [], []
        )
        result = self.MATCHER.analyze(nypl_rl_bib, candidates=candidates)
        assert result.call_number_match is False
        assert result.action == "update"
        assert result.target_bib_id == "12345"
        assert result.call_number == nypl_rl_bib.call_number
        assert result.target_call_no is None

    def test_analyze_no_matches(self, nypl_rl_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.MATCHER.analyze(nypl_rl_bib, candidates=candidates)
        assert result.target_bib_id is None
        assert result.action == "insert"
        assert result.call_number == nypl_rl_bib.call_number
        assert result.call_number_match is True
        assert result.target_call_no == nypl_rl_bib.call_number
        assert result.target_title is None


class TestNYPLCatBranchMatchAnalyzer:
    MATCHER = matching.NYPLCatBranchMatchAnalyzer()

    @pytest.mark.parametrize("call_number, match", [("Foo", True), ("Bar", False)])
    def test_analyze(self, nypl_bl_bib, nypl_bl_data, call_number, match):
        nypl_bl_bib.branch_call_number = call_number
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(nypl_bl_data)], [], []
        )
        result = self.MATCHER.analyze(nypl_bl_bib, candidates=candidates)
        assert result.call_number_match == match
        assert result.target_call_no == "Foo"

    def test_analyze_no_response_call_no(self, nypl_bl_bib, nypl_bl_data):
        data = copy.deepcopy(nypl_bl_data)
        data["varFields"] = [i for i in data["varFields"] if i["marcTag"] != "091"]
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(data)], [], []
        )
        result = self.MATCHER.analyze(nypl_bl_bib, candidates=candidates)
        assert result.call_number_match is False

    def test_analyze_no_matches(self, nypl_bl_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.MATCHER.analyze(nypl_bl_bib, candidates=candidates)
        assert result.target_bib_id is None
        assert result.action == "insert"
        assert result.call_number == nypl_bl_bib.call_number
        assert result.call_number_match is True
        assert result.target_call_no == nypl_bl_bib.call_number
        assert result.target_title is None


class TestSelectionMatchAnalyzer:
    MATCHER = matching.SelectionMatchAnalyzer()

    def test_analyze_bl(self, bpl_bib, bpl_data):
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.BPLSolrResponse(bpl_data)], [], []
        )
        result = self.MATCHER.analyze(bpl_bib, candidates=candidates)
        assert result.call_number_match is True
        assert result.target_call_no == "Foo"
        assert result.action == "attach"
        assert result.call_number_match is True

    def test_analyze_rl(self, nypl_rl_bib, nypl_rl_data):
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(nypl_rl_data)], [], []
        )
        result = self.MATCHER.analyze(nypl_rl_bib, candidates=candidates)
        assert result.call_number_match is True
        assert result.target_call_no == "Foo"
        assert result.action == "attach"
        assert result.call_number_match is True

    def test_analyze_no_matches(self, nypl_bl_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.MATCHER.analyze(nypl_bl_bib, candidates=candidates)
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.target_call_no is None
        assert result.target_title is None
        assert result.target_bib_id is None

    def test_analyze_no_call_number(self, nypl_bl_bib, nypl_bl_data):
        nypl_bl_data["varFields"] = [
            i for i in nypl_bl_data["varFields"] if i["marcTag"] in ["901", "910"]
        ]
        candidates = matching.ClassifiedCandidates(
            [sierra_responses.NYPLPlatformResponse(nypl_bl_data)], [], []
        )
        result = self.MATCHER.analyze(nypl_bl_bib, candidates=candidates)
        assert result.target_bib_id == "12345"
        assert result.call_number is None
        assert result.action == "attach"
        assert result.call_number_match is True
        assert result.target_call_no is None
