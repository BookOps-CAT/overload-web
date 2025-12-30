import datetime
import json

import pytest

from overload_web.bib_records.domain import bib_services, bibs, marc_protocols
from overload_web.bib_records.infrastructure import response_reviewer, sierra_responses

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


def stub_sierra_response(stub_order_bib, library, collection):
    responses = FakeBibFetcher(library=library, collection=collection).get_bibs_by_id(
        key="isbn", value="9781234567890"
    )
    return bibs.MatcherResponse(bib=stub_order_bib, matches=responses)


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


@pytest.mark.parametrize(
    "library, collection",
    [
        ("nypl", "BL"),
        ("nypl", "RL"),
        ("bpl", "NONE"),
    ],
)
class TestReviewer:
    @pytest.fixture
    def stub_full_response(self, stub_full_bib, library, collection):
        responses = FakeBibFetcher(
            library=library, collection=collection
        ).get_bibs_by_id(key="isbn", value="9781234567890")
        return bibs.MatcherResponse(bib=stub_full_bib, matches=responses)

    @pytest.fixture
    def stub_order_response(self, stub_order_bib, library, collection):
        responses = FakeBibFetcher(
            library=library, collection=collection
        ).get_bibs_by_id(key="isbn", value="9781234567890")
        return bibs.MatcherResponse(bib=stub_order_bib, matches=responses)

    def test_attach_acq(self, library, collection, stub_order_response):
        stub_service = bib_services.BibReviewer(
            reviewer=response_reviewer.ReviewerFactory().make(
                record_type="acq", collection=collection, library=library
            )
        )
        attached_bibs = stub_service.review_and_attach([stub_order_response])
        assert attached_bibs[0].bib_id is None
        assert stub_order_response.bib.bib_id is None

    def test_attach_cat(self, library, collection, stub_full_response):
        stub_service = bib_services.BibReviewer(
            reviewer=response_reviewer.ReviewerFactory().make(
                record_type="cat", collection=collection, library=library
            )
        )
        attached_bibs = stub_service.review_and_attach([stub_full_response])
        assert attached_bibs[0].bib_id == "123"

    def test_attach_sel(self, library, collection, stub_order_response):
        stub_service = bib_services.BibReviewer(
            reviewer=response_reviewer.ReviewerFactory().make(
                record_type="sel", collection=collection, library=library
            )
        )
        attached_bibs = stub_service.review_and_attach([stub_order_response])
        assert attached_bibs[0].bib_id == "123"

    def test_reviewer_factory(self, library, collection):
        with pytest.raises(ValueError) as exc:
            response_reviewer.ReviewerFactory().make(
                record_type="foo", collection=collection, library=library
            )
        assert str(exc.value) == "Invalid library/record_type/collection combination"


class TestBaseReviewer:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results_bpl(self, sierra_response, new_domain_bib):
        new_domain_bib.isbn = None
        review = response_reviewer.BaseReviewer()
        review.sort_results(new_domain_bib, results=[sierra_response, sierra_response])
        assert new_domain_bib.bib_id is None
        assert review.duplicate_records == ["12345", "12345"]
        assert review.input_call_no == "Foo"
        assert review.resource_id is None
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

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_results_nypl(self, sierra_response, new_domain_bib, collection):
        new_domain_bib.isbn = None
        review = response_reviewer.BaseReviewer()
        review.sort_results(new_domain_bib, results=[sierra_response, sierra_response])
        assert new_domain_bib.bib_id is None
        assert review.duplicate_records == ["12345", "12345"]
        assert review.input_call_no == "Foo"
        assert review.resource_id is None
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

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    def test_review_results_no_results(self, new_domain_bib):
        review = response_reviewer.BaseReviewer()
        review.sort_results(new_domain_bib, results=[])
        assert review.duplicate_records == []

    @pytest.mark.parametrize(
        "library, collection", [("bpl", "NONE"), ("nypl", "BL"), ("nypl", "RL")]
    )
    @pytest.mark.parametrize("key", ["bib_id", "control_number", "oclc_number", "upc"])
    def test_review_results_resource_id(self, new_domain_bib, key):
        new_domain_bib.isbn = None
        setattr(new_domain_bib, key, "987654321")
        review = response_reviewer.BaseReviewer()
        review.sort_results(new_domain_bib, results=[])
        assert review.resource_id == "987654321"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_results_mixed(self, new_domain_bib):
        data = {k: v for k, v in NYPL_DATA.items()}
        data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
        )
        data["varFields"].append(
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
        )
        response = sierra_responses.NYPLPlatformResponse(data=data)
        review = response_reviewer.BaseReviewer()
        review.sort_results(new_domain_bib, results=[response])
        assert len(review.mixed_results) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_results_unmatched(self, new_domain_bib, sierra_response):
        new_domain_bib.collection = "NONE"
        review = response_reviewer.BaseReviewer()
        review.sort_results(new_domain_bib, results=[sierra_response])
        assert len(review.other_results) == 1
        assert len(review.matched_results) == 0


class TestSelectionReviewer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_review_results(self, sierra_response, new_domain_bib):
        review = response_reviewer.SelectionReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert review.resource_id == "9781234567890"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_results_no_call_no(self, new_domain_bib, collection):
        resp_data = {k: v for k, v in NYPL_DATA.items() if k != "varFields"}
        resp_data["varFields"] = [
            {
                "marcTag": "910",
                "subfields": [{"content": collection, "tag": "a"}],
            }
        ]
        response = sierra_responses.NYPLPlatformResponse(data=resp_data)
        review = response_reviewer.SelectionReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert new_domain_bib.bib_id is None
        assert response.bib_id == "12345"
        assert response.branch_call_number is None
        assert response.research_call_number == []
        assert len(review.matched_results) > 0
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"
        assert len(review.results) == 1
        assert review.results[0].branch_call_number is None
        assert review.results[0].research_call_number == []

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_review_results_no_results(self, new_domain_bib):
        review = response_reviewer.SelectionReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None


class TestAcquisitionsReviewer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_review_results(self, sierra_response, new_domain_bib):
        review = response_reviewer.AcquisitionsReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result is None
        assert review.duplicate_records == []


class TestNYPLBranchReviewer:
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results(self, sierra_response, new_domain_bib):
        review = response_reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results_no_results(self, new_domain_bib):
        review = response_reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results_vendor_record(self, new_domain_bib):
        data = {k: v for k, v in NYPL_DATA.items()}
        data["varFields"] = [i for i in NYPL_DATA["varFields"] if i["marcTag"] != "901"]
        response = sierra_responses.NYPLPlatformResponse(data)
        review = response_reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "12345"
        assert response.update_datetime < new_domain_bib.update_datetime

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results_no_call_no_match_inhouse(self, new_domain_bib):
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
        review = response_reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "23456"
        assert response.cat_source == "inhouse"
        assert review.action == "attach"

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    @pytest.mark.parametrize(
        "date, action",
        [("2025-01-01T01:00:00", "overlay"), ("2020-01-01T01:00:00", "attach")],
    )
    def test_review_results_no_call_no_match_vendor(self, new_domain_bib, date, action):
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
        review = response_reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "34567"
        assert response.cat_source == "vendor"
        assert response.branch_call_number is not None
        assert review.call_number_match is False
        assert review.action == action

    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_results_no_call_no(self, new_domain_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]}
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        review = response_reviewer.NYPLBranchReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "34567"
        assert response.branch_call_number is None
        assert review.call_number_match is False
        assert review.action == "overlay"


class TestNYPLResearchReviewer:
    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_review_results(self, sierra_response, new_domain_bib):
        review = response_reviewer.NYPLResearchReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_review_results_no_results(self, new_domain_bib):
        review = response_reviewer.NYPLResearchReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    @pytest.mark.parametrize(
        "date, action",
        [("2025-01-01T01:00:00", "overlay"), ("2020-01-01T01:00:00", "attach")],
    )
    def test_review_results_vendor_record(self, new_domain_bib, date, action):
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
        review = response_reviewer.NYPLResearchReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "34567"
        assert response.cat_source == "vendor"
        assert len(response.research_call_number) > 0
        assert review.call_number_match is True
        assert review.action == action

    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_review_results_no_call_no(self, new_domain_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "updatedDate": "2020-01-01T01:00:00",
            "varFields": [
                {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]}
            ],
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        review = response_reviewer.NYPLResearchReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "34567"
        assert response.research_call_number == []
        assert review.call_number_match is False
        assert review.action == "overlay"


class TestBPLReviewer:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results(self, sierra_response, new_domain_bib):
        review = response_reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[sierra_response])
        assert new_domain_bib.bib_id is None
        assert result == "12345"
        assert review.duplicate_records == []
        assert review.input_call_no == "Foo"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results_no_results(self, new_domain_bib):
        review = response_reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[])
        assert new_domain_bib.bib_id is None
        assert result is None

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results_no_results_midwest(self, make_domain_bib):
        domain_bib = make_domain_bib(
            {
                "037": {"code": "b", "value": "Midwest"},
                "099": {"code": "a", "value": "DVD"},
            },
            "cat",
        )
        review = response_reviewer.BPLReviewer()
        result = review.review_results(domain_bib, results=[])
        assert domain_bib.bib_id is None
        assert result is None

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_review_results_vendor_record(self, new_domain_bib, date, action):
        data = {
            "id": "12345",
            "title": "Record 2",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        response = sierra_responses.BPLSolrResponse(data)
        review = response_reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "12345"
        assert review.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results_no_call_no_match_inhouse(self, new_domain_bib):
        data = {
            "id": "23456",
            "title": "Record 2",
            "ss_marc_tag_005": "20200101010000.0",
            "ss_marc_tag_001": "ocn123456789",
            "ss_marc_tag_003": "OCoLC",
            "call_number": "Bar",
        }
        response = sierra_responses.BPLSolrResponse(data)
        review = response_reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "23456"
        assert response.cat_source == "inhouse"
        assert review.action == "attach"

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    @pytest.mark.parametrize(
        "date, action",
        [("20250101010000.0", "overlay"), ("20200101010000.0", "attach")],
    )
    def test_review_results_no_call_no_match_vendor(self, new_domain_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Baz",
        }
        response = sierra_responses.BPLSolrResponse(data)
        review = response_reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "34567"
        assert response.cat_source == "vendor"
        assert review.action == action

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_review_results_no_call_no(self, new_domain_bib):
        data = {"id": "34567", "title": "Record 3"}
        response = sierra_responses.BPLSolrResponse(data)
        review = response_reviewer.BPLReviewer()
        result = review.review_results(new_domain_bib, results=[response])
        assert result == "34567"
        assert review.action == "overlay"
