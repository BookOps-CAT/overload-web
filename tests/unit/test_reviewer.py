import datetime
import json

import pytest

from overload_web.bib_records.domain_models import (
    marc_protocols,
    sierra_responses,
)
from overload_web.bib_records.domain_services import review

BPL_DATA = {
    "call_number": "Foo",
    "id": "12345",
    "isbn": ["9781234567890"],
    "sm_bib_varfields": ["099 || {{a}} Foo"],
    "sm_item_data": ['{"barcode": "33333123456789"}'],
    "ss_marc_tag_001": "ocn123456789",
    "ss_marc_tag_003": "OCoLC",
    "ss_marc_tag_005": "20000101010000.0",
    "title": "Record 1",
}
NYPL_DATA = {
    "id": "12345",
    "controlNumber": "ocn123456789",
    "standardNumbers": ["9781234567890"],
    "title": "Record 1",
    "updatedDate": "2000-01-01T01:00:00",
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


class StubFetcher(marc_protocols.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def __init__(self, library, collection):
        super().__init__()
        self.library = library
        self.collection = collection

    def get_bibs_by_id(self, value, key):
        if str(self.library) == "nypl":
            file = f"tests/data/{str(self.library)}_{str(self.collection)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["data"]
            return [sierra_responses.NYPLPlatformResponse(data=i) for i in data]
        else:
            file = f"tests/data/{str(self.library)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["response"]["docs"]
            return [sierra_responses.BPLSolrResponse(data=i) for i in data]


@pytest.fixture
def new_domain_bib(make_domain_bib, library):
    bib = make_domain_bib({}, "cat")
    bib.update_date = "20200101010000.0"
    return bib


@pytest.fixture
def sierra_response(library, collection):
    if library == "bpl":
        return sierra_responses.BPLSolrResponse(data=BPL_DATA)
    NYPL_DATA["varFields"] = [
        i for i in NYPL_DATA["varFields"] if i["marcTag"] != "910"
    ]
    if collection == "BL":
        NYPL_DATA["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
        )
        return sierra_responses.NYPLPlatformResponse(data=NYPL_DATA)
    elif collection == "RL":
        NYPL_DATA["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        )
        return sierra_responses.NYPLPlatformResponse(data=NYPL_DATA)


class TestReviewer:
    @pytest.mark.parametrize(
        "library, collection",
        [
            ("nypl", "BL"),
            ("nypl", "RL"),
            ("bpl", "NONE"),
        ],
    )
    def test_base_analyzer(self, stub_acq_bib, sierra_response, library, collection):
        service = review.BaseMatchAnalyzer()
        with pytest.raises(NotImplementedError):
            service.resolve(stub_acq_bib, candidates=[sierra_response])

    @pytest.mark.parametrize(
        "library, collection",
        [
            ("nypl", "BL"),
            ("nypl", "RL"),
            ("bpl", "NONE"),
        ],
    )
    def test_attach_acq(self, stub_acq_bib, library, collection):
        stub_acq_response = sierra_responses.MatcherResponse(
            bib=stub_acq_bib,
            matches=FakeBibFetcher(
                library=library, collection=collection
            ).get_bibs_by_id(key="isbn", value="9781234567890"),
        )
        stub_service = review.AcquisitionsMatchAnalyzer()
        attached_bibs = stub_service.review_candidates([stub_acq_response])
        assert attached_bibs[1][0].bib_id is None
        assert stub_acq_response.bib.bib_id is None

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_attach_cat_bpl(self, stub_cat_bib, library, collection):
        stub_cat_response = sierra_responses.MatcherResponse(
            bib=stub_cat_bib,
            matches=FakeBibFetcher(
                library=library, collection=collection
            ).get_bibs_by_id(key="isbn", value="9781234567890"),
        )
        stub_service = review.BPLCatMatchAnalyzer()
        attached_bibs = stub_service.review_candidates([stub_cat_response])
        assert attached_bibs[1][0].bib_id == "123"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_attach_cat_nypl_bl(self, stub_cat_bib, library, collection):
        stub_cat_response = sierra_responses.MatcherResponse(
            bib=stub_cat_bib,
            matches=FakeBibFetcher(
                library=library, collection=collection
            ).get_bibs_by_id(key="isbn", value="9781234567890"),
        )
        stub_service = review.NYPLCatBranchMatchAnalyzer()
        attached_bibs = stub_service.review_candidates([stub_cat_response])
        assert attached_bibs[1][0].bib_id == "123"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_attach_cat_nypl_rl(self, stub_cat_bib, library, collection):
        stub_cat_response = sierra_responses.MatcherResponse(
            bib=stub_cat_bib,
            matches=FakeBibFetcher(
                library=library, collection=collection
            ).get_bibs_by_id(key="isbn", value="9781234567890"),
        )
        stub_service = review.NYPLCatResearchMatchAnalyzer()
        attached_bibs = stub_service.review_candidates([stub_cat_response])
        assert attached_bibs[1][0].bib_id == "123"

    @pytest.mark.parametrize(
        "library, collection",
        [
            ("nypl", "BL"),
            ("nypl", "RL"),
            ("bpl", "NONE"),
        ],
    )
    def test_attach_sel(self, stub_sel_bib, library, collection):
        stub_sel_response = sierra_responses.MatcherResponse(
            bib=stub_sel_bib,
            matches=FakeBibFetcher(
                library=library, collection=collection
            ).get_bibs_by_id(key="isbn", value="9781234567890"),
        )
        stub_service = review.SelectionMatchAnalyzer()
        attached_bibs = stub_service.review_candidates([stub_sel_response])
        assert attached_bibs[1][0].bib_id == "123"


class TestCandidateClassifier:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_bpl(self, sierra_response, new_domain_bib):
        new_domain_bib.isbn = None
        classified = review.CandidateClassifier.classify(
            new_domain_bib, candidates=[sierra_response, sierra_response]
        )
        assert new_domain_bib.bib_id is None
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
        assert review.get_resource_id(new_domain_bib) is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_nypl(self, sierra_response, new_domain_bib, collection):
        new_domain_bib.isbn = None
        classified = review.CandidateClassifier.classify(
            new_domain_bib, candidates=[sierra_response, sierra_response]
        )
        assert new_domain_bib.bib_id is None
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
        assert review.get_resource_id(new_domain_bib) is None

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_resolve_no_results(self, new_domain_bib):
        classified = review.CandidateClassifier.classify(new_domain_bib, candidates=[])
        assert classified.duplicates == []

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    @pytest.mark.parametrize("key", ["bib_id", "control_number", "oclc_number", "upc"])
    def test_resolve_resource_id(self, new_domain_bib, key):
        new_domain_bib.isbn = None
        setattr(new_domain_bib, key, "987654321")
        resource_id = review.get_resource_id(new_domain_bib)
        assert resource_id == "987654321"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_mixed(self, new_domain_bib):
        data = {k: v for k, v in NYPL_DATA.items()}
        data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
        )
        data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        )
        response = sierra_responses.NYPLPlatformResponse(data=data)
        classified = review.CandidateClassifier.classify(
            new_domain_bib, candidates=[response]
        )
        assert len(classified.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_unmatched(self, new_domain_bib, sierra_response):
        new_domain_bib.collection = "NONE"
        classified = review.CandidateClassifier.classify(
            new_domain_bib, candidates=[sierra_response]
        )

        assert len(classified.other) == 1
        assert len(classified.matched) == 0


class TestSelectionMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_resolve(self, sierra_response, new_domain_bib):
        reviewer = review.SelectionMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"
        assert result.resource_id == "9781234567890"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_resolve_no_call_no(self, new_domain_bib, collection):
        resp_data = {k: v for k, v in NYPL_DATA.items() if k != "varFields"}
        resp_data["varFields"] = [
            {
                "marcTag": "910",
                "subfields": [{"content": collection, "tag": "a"}],
            }
        ]
        response = sierra_responses.NYPLPlatformResponse(data=resp_data)
        reviewer = review.SelectionMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert new_domain_bib.bib_id is None
        assert response.bib_id == "12345"
        assert response.branch_call_number is None
        assert response.research_call_number == []
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_resolve_no_results(self, new_domain_bib):
        reviewer = review.SelectionMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id is None


class TestAcquisitionsMatchAnalyzer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_resolve(self, sierra_response, new_domain_bib):
        reviewer = review.AcquisitionsMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.duplicate_records == []


class TestNYPLCatBranchMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve(self, sierra_response, new_domain_bib):
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_no_results(self, new_domain_bib):
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_vendor_record(self, new_domain_bib):
        data = {k: v for k, v in NYPL_DATA.items()}
        data["varFields"] = [i for i in NYPL_DATA["varFields"] if i["marcTag"] != "901"]
        response = sierra_responses.NYPLPlatformResponse(data)
        reviewer = review.NYPLCatBranchMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "12345"
        assert response.update_datetime < new_domain_bib.update_datetime

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_no_call_no_match_inhouse(self, new_domain_bib):
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
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "23456"
        assert response.cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    @pytest.mark.parametrize(
        "date, action",
        [("2025-01-01T01:00:00", "overlay"), ("2020-01-01T01:00:00", "attach")],
    )
    def test_resolve_no_call_no_match_vendor(self, new_domain_bib, date, action):
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
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert response.branch_call_number is not None
        assert result.call_number_match is False
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_resolve_no_call_no(self, new_domain_bib):
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
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.branch_call_number is None
        assert result.call_number_match is False
        assert result.action == "overlay"


class TestNYPLCatResearchMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_resolve(self, sierra_response, new_domain_bib):
        reviewer = review.NYPLCatResearchMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_resolve_no_results(self, new_domain_bib):
        reviewer = review.NYPLCatResearchMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id is None

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    @pytest.mark.parametrize(
        "date, action",
        [("2025-01-01T01:00:00", "overlay"), ("2020-01-01T01:00:00", "attach")],
    )
    def test_resolve_vendor_record(self, new_domain_bib, date, action):
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
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert len(response.research_call_number) > 0
        assert result.call_number_match is True
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_resolve_no_call_no(self, new_domain_bib):
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
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.research_call_number == []
        assert result.call_number_match is False
        assert result.action == "overlay"


class TestBPLCatMatchAnalyzer:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve(self, sierra_response, new_domain_bib):
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_results(self, new_domain_bib):
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[])
        assert new_domain_bib.bib_id is None
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
    def test_resolve_vendor_record(self, new_domain_bib, date, action):
        data = {
            "id": "12345",
            "title": "Record 2",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "12345"
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_call_no_match_inhouse(self, new_domain_bib):
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
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "23456"
        assert response.cat_source == "inhouse"
        assert result.action == "attach"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_resolve_no_call_no_match_vendor(self, new_domain_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Baz",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert result.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_resolve_no_call_no(self, new_domain_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": "20250101010000.0",
        }
        response = sierra_responses.BPLSolrResponse(data)
        reviewer = review.BPLCatMatchAnalyzer()
        result = reviewer.resolve(new_domain_bib, candidates=[response])
        assert result.target_bib_id == "34567"
        assert result.action == "overlay"
