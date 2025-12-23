import datetime

import pytest

from overload_web.bib_records.infrastructure.sierra import responses, reviewer

BPL_DATA = {
    "call_number": "Foo",
    "id": "12345",
    "isbn": ["9781234567890"],
    "sm_bib_varfields": [],
    "sm_item_data": ['{"barcode": "33333123456789"}'],
    "ss_marc_tag_001": "ocn123456789",
    "ss_marc_tag_003": "OCoLC",
    "ss_marc_tag_005": "20200101010000.0",
    "title": "Record 1",
}
NYPL_DATA = {
    "id": "12345",
    "controlNumber": "ocn123456789",
    "standardNumbers": ["9781234567890"],
    "title": "Record 1",
    "updatedDate": "2020-01-01T01:00:00",
    "varFields": [
        {"marcTag": "091", "subfields": [{"content": "Foo", "tag": "a"}]},
        {
            "ind1": "8",
            "ind2": " ",
            "marcTag": "852",
            "subfields": [{"content": "Foo", "tag": "a"}],
        },
        {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
    ],
}


@pytest.fixture
def new_domain_bib(make_full_bib, library):
    bib = make_full_bib({"020": {"code": "a", "value": "9781234567890"}})
    bib.update_date = "20250101010000.0"
    return bib


class TestResponses:
    def test_bpl_response_from_dict(self):
        response = responses.BPLSolrResponse(data=BPL_DATA)
        assert response.bib_id == "12345"
        assert response.barcodes == ["33333123456789"]
        assert response.branch_call_number == ["Foo"]
        assert response.cat_source == "inhouse"
        assert response.collection is None
        assert response.control_number == "ocn123456789"
        assert response.isbn == ["9781234567890"]
        assert response.oclc_number == ["ocn123456789"]
        assert response.research_call_number == []
        assert response.upc == []
        assert response.update_date == "20200101010000.0"
        assert response.update_datetime == datetime.datetime(2020, 1, 1, 1, 0, 0, 0)
        assert response.var_fields == []

    def test_nypl_rl_response_from_dict(self):
        NYPL_DATA["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        )
        response = responses.NYPLPlatformResponse(data=NYPL_DATA)
        assert response.bib_id == "12345"
        assert response.barcodes == []
        assert response.branch_call_number == ["Foo"]
        assert response.cat_source == "inhouse"
        assert response.control_number == "ocn123456789"
        assert response.isbn == ["9781234567890"]
        assert response.oclc_number == ["ocn123456789"]
        assert response.research_call_number == ["Foo"]
        assert response.upc == []
        assert response.update_date == "2020-01-01T01:00:00"
        assert response.update_datetime == datetime.datetime(2020, 1, 1, 1, 0, 0, 0)
        assert len(response.var_fields) == 4


@pytest.fixture
def nypl_bl_response():
    NYPL_DATA["varFields"] = [
        i for i in NYPL_DATA["varFields"] if i["marcTag"] != "910"
    ]
    NYPL_DATA["varFields"].append(
        {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
    )
    return responses.NYPLPlatformResponse(data=NYPL_DATA)


@pytest.fixture
def nypl_rl_response():
    NYPL_DATA["varFields"] = [
        i for i in NYPL_DATA["varFields"] if i["marcTag"] != "910"
    ]
    NYPL_DATA["varFields"].append(
        {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
    )
    return responses.NYPLPlatformResponse(data=NYPL_DATA)


@pytest.fixture
def bpl_response():
    return responses.BPLSolrResponse(data=BPL_DATA)


@pytest.fixture
def sierra_response(library, collection):
    if library == "bpl":
        return responses.BPLSolrResponse(data=BPL_DATA)
    NYPL_DATA["varFields"] = [
        i for i in NYPL_DATA["varFields"] if i["marcTag"] != "910"
    ]
    if collection == "BL":
        NYPL_DATA["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
        )
        return responses.NYPLPlatformResponse(data=NYPL_DATA)
    elif collection == "RL":
        NYPL_DATA["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        )
        return responses.NYPLPlatformResponse(data=NYPL_DATA)


class TestBaseReviewer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_review_results(self, sierra_response, new_domain_bib):
        new_domain_bib.isbn = None
        review = reviewer.BaseReviewer()
        review._sort_results(new_domain_bib, results=[sierra_response, sierra_response])
        assert new_domain_bib.bib_id is None
        assert review.duplicate_records == ["12345", "12345"]
        assert review.input_call_no == "Foo"
        assert review.resource_id is None

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_review_results_no_results(self, new_domain_bib):
        review = reviewer.BaseReviewer()
        review._sort_results(new_domain_bib, results=[])
        assert review.duplicate_records == []

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    @pytest.mark.parametrize("key", ["bib_id", "control_number", "oclc_number", "upc"])
    def test_review_results_resource_id(self, new_domain_bib, key):
        new_domain_bib.isbn = None
        setattr(new_domain_bib, key, "987654321")
        review = reviewer.BaseReviewer()
        review._sort_results(new_domain_bib, results=[])
        assert review.resource_id == "987654321"


class TestSelectionReviewer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_review_results(self, sierra_response, new_domain_bib):
        review = reviewer.SelectionReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert review.resource_id == "9781234567890"


class TestAcquisitionsReviewer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_review_results(self, sierra_response, new_domain_bib):
        review = reviewer.AcquisitionsReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result is None
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert review.resource_id == "9781234567890"


class TestNYPLBranchReviewer:
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results(self, sierra_response, new_domain_bib):
        review = reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert review.resource_id == "9781234567890"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results_no_matches(self, new_domain_bib):
        review = reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None


class TestNYPLResearchReviewer:
    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_review_results(self, sierra_response, new_domain_bib):
        review = reviewer.NYPLResearchReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert review.resource_id == "9781234567890"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_review_results_no_matches(self, new_domain_bib):
        review = reviewer.NYPLResearchReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None


class TestBPLReviewer:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results(self, sierra_response, new_domain_bib):
        review = reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert review.resource_id == "9781234567890"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results_no_matches(self, new_domain_bib):
        review = reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None
