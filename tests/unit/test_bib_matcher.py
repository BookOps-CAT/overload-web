import datetime
from contextlib import nullcontext as does_not_raise

import pytest

from overload_web.application.pvf import match_service
from overload_web.domain.pvf import models
from overload_web.domain.shared import sierra_responses
from overload_web.infrastructure import sierra_clients


@pytest.fixture
def stub_domain_bib(library, collection):
    return models.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type="acq",
        binary_data=b"",
        control_number="12345",
        parsed_fields=[],
    )


@pytest.fixture
def nypl_data():
    return {
        "id": "12345",
        "title": "Record 1",
        "updatedDate": "2020-01-01T01:00:00",
        "varFields": [],
        "locations": [
            {"code": "a", "name": "library"},
            {"code": "123", "name": "library"},
        ],
    }


@pytest.fixture
def stub_matcher(fake_fetcher):
    return match_service.BibMatcher(fetcher=fake_fetcher)


class TestSierraBibFetcher:
    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "control_number"])
    def test_get_bibs_by_id_bpl(self, mock_sierra_session, match, caplog):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert "Querying Sierra with BPLSolrSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "BPLSolrSession"

    @pytest.mark.parametrize("id", [".b123", ".i123", ".o123", "123", 123, 123456789])
    def test_get_bibs_by_bib_id_bpl(self, mock_sierra_session, id):
        """Test `_prep_sierra_number override."""
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "control_number"])
    def test_get_bibs_by_id_nypl(self, mock_sierra_session, match, caplog):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert "Querying Sierra with NYPLPlatformSession" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == "NYPLPlatformSession"

    @pytest.mark.parametrize("id", [".b123", ".i123", ".o123", "123", 123, 123456789])
    def test_get_bibs_by_bib_id_nypl(self, mock_sierra_session, id):
        """Test `_prep_sierra_number override."""
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        with does_not_raise():
            fetcher.get_bibs_by_id(value=id, key="bib_id")

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_sierra_session, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert "Unsupported query matchpoint: 'bar'" in caplog.text
        assert "Invalid matchpoint: 'bar'. Available matchpoints are:" in str(exc.value)

    @pytest.mark.parametrize(
        "match", ["bib_id", "upc", "isbn", "control_number", "issn"]
    )
    def test_get_bibs_by_id_no_value_passed(self, match, mock_sierra_session, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_sierra_session)
        bibs = fetcher.get_bibs_by_id(value=None, key=match)
        assert bibs == []
        assert f"Skipping Sierra query on {match} with missing value." in caplog.text

    def test_get_bibs_by_id_nypl_error(self, mock_nypl_session_error, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_nypl_session_error)
        with pytest.raises(sierra_clients.BookopsPlatformError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsPlatformError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_bpl_error(self, mock_bpl_session_error, caplog):
        fetcher = sierra_clients.SierraBibFetcher(session=mock_bpl_session_error)
        with pytest.raises(sierra_clients.BookopsSolrError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsSolrError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_nypl_issn(self, mock_sierra_session):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.NYPLPlatformSession()
        )
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in NYPL Platform" in str(exc.value)

    def test_get_bibs_by_id_bpl_issn(self, mock_sierra_session):
        fetcher = sierra_clients.SierraBibFetcher(
            session=sierra_clients.BPLSolrSession()
        )
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in BPL Solr" in str(exc.value)


class TestFetcherFactory:
    @pytest.mark.parametrize(
        "library, session_type",
        [("nypl", "NYPLPlatformSession"), ("bpl", "BPLSolrSession")],
    )
    def test_fetcher_factory(self, mock_sierra_session, library, session_type):
        fetcher = sierra_clients.FetcherFactory.make(library=library)
        assert isinstance(fetcher, sierra_clients.SierraBibFetcher)
        assert fetcher.session.__class__.__name__ == session_type

    def test_fetcher_factory_invalid_library(self, mock_sierra_session):
        with pytest.raises(ValueError) as exc:
            sierra_clients.FetcherFactory.make(library="foo")
        assert str(exc.value) == "Invalid library: foo. Must be 'bpl' or 'nypl'"

    def test_fetcher_factory_platform_error(self, mock_nypl_session_error):
        with pytest.raises(sierra_clients.BookopsPlatformError) as exc:
            sierra_clients.FetcherFactory.make(library="nypl")
        assert "Trouble connecting: " in str(exc.value)


@pytest.mark.parametrize(
    "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", None)]
)
class TestBibMatcher:
    @pytest.mark.parametrize(
        "matchpoints",
        [{"primary_matchpoint": "isbn"}, {"primary_matchpoint": "control_number"}],
    )
    def test_match_full(self, stub_domain_bib, matchpoints, stub_matcher):
        stub_domain_bib.vendor_info = models.VendorInfo(
            name="UNKNOWN", matchpoints=matchpoints, bib_fields=[]
        )
        stub_domain_bib.record_type = "cat"
        candidates = stub_matcher.match_full_record(stub_domain_bib)
        assert len(candidates) == 1

    @pytest.mark.parametrize(
        "matchpoints",
        [{"primary_matchpoint": "isbn"}, {"primary_matchpoint": "control_number"}],
    )
    def test_match_full_no_candidates(
        self, fake_fetcher_no_matches, stub_domain_bib, matchpoints
    ):
        stub_domain_bib.vendor_info = models.VendorInfo(
            name="UNKNOWN", matchpoints=matchpoints, bib_fields=[]
        )
        stub_domain_bib.record_type = "cat"
        service = match_service.BibMatcher(fetcher=fake_fetcher_no_matches)
        candidates = service.match_full_record(stub_domain_bib)
        assert len(candidates) == 0

    def test_match_full_no_vendor_index(self, stub_domain_bib, stub_matcher):
        stub_domain_bib.record_type = "cat"
        assert stub_domain_bib.vendor_info is None
        with pytest.raises(ValueError) as exc:
            stub_matcher.match_full_record(stub_domain_bib)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_order_level(self, stub_domain_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            stub_domain_bib, matchpoints={"primary_matchpoint": "upc"}
        )
        assert len(candidates) == 0

    def test_match_order_level_no_matchpoints(self, stub_domain_bib, stub_matcher):
        with pytest.raises(TypeError) as exc:
            stub_matcher.match_order_record(stub_domain_bib)
        assert (
            str(exc.value)
            == "BibMatcher.match_order_record() missing 1 required positional argument: 'matchpoints'"
        )

    def test_match_order_level_none(self, stub_domain_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            stub_domain_bib, matchpoints={"primary_matchpoint": None}
        )
        assert len(candidates) == 0

    def test_action_attr(self, acq_bib):
        with pytest.raises(AttributeError) as exc:
            acq_bib.action
        assert str(exc.value) == "CatalogAction has not been assigned to the DomainBib"

    @pytest.mark.parametrize(
        "key, value, output",
        [
            ("control_number", "123456789", "123456789"),
            ("isbn", "123456789", "123456789"),
            ("oclc_number", [], None),
            ("oclc_number", "123456789", "123456789"),
            ("oclc_number", ["123456789", "987654321"], "123456789"),
            ("upc", "123456789", "123456789"),
        ],
    )
    def test_review_matches_acq(
        self, acq_bib, stub_matcher, key, value, sierra_response, output
    ):
        acq_bib.isbn = None
        setattr(acq_bib, key, value)
        result = stub_matcher.review_matches(
            acq_bib, matches=[sierra_response, sierra_response]
        )
        assert acq_bib.bib_id is None
        assert result.target_bib_id == acq_bib.bib_id
        assert result.duplicate_records == ["12345", "12345"]
        assert result.resource_id == output
        assert result.mixed == []
        assert result.other == []
        assert result.action == "insert"
        assert result.call_number_match is True
        assert result.updated_by_vendor is False
        assert result.target_call_no == result.call_number
        assert result.target_title == acq_bib.title

    def test_review_matches_cat(self, full_bib, stub_matcher, sierra_response):
        result = stub_matcher.review_matches(full_bib, matches=[sierra_response])
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

    def test_review_matches_cat_no_matches(self, full_bib, stub_matcher):
        result = stub_matcher.review_matches(full_bib, matches=[])
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

    def test_review_matches_sel(self, sel_bib, stub_matcher, sierra_response):
        result = stub_matcher.review_matches(sel_bib, matches=[sierra_response])
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

    def test_review_matches_sel_no_matches(self, sel_bib, stub_matcher):
        result = stub_matcher.review_matches(sel_bib, matches=[])
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

    def test_review_matches_sel_no_call_no(
        self, sel_bib, sierra_response, stub_matcher, collection
    ):
        sierra_response["varFields"] = [
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]},
        ]
        sierra_response = {
            k: v for k, v in sierra_response.items() if k != "call_number"
        }
        result = stub_matcher.review_matches(sel_bib, matches=[sierra_response])
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


class TestBibMatcherReviewMatches:
    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "update", True),
            ("2020-01-01T01:00:00", "attach", False),
            (None, "attach", False),
        ],
    )
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_matches_cat_bl_vendor_record(
        self, full_bib, date, action, updated, nypl_data, stub_matcher
    ):
        nypl_data["varFields"] = [
            {
                "marcTag": "091",
                "ind1": " ",
                "ind2": " ",
                "subfields": [{"content": "Foo", "tag": "a"}],
            }
        ]
        nypl_data["updatedDate"] = date
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.action == action
        assert result.mixed == []
        assert result.other == []
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.call_number_match is True
        assert result.updated_by_vendor == updated
        assert result.target_call_no == "Foo"
        assert result.target_title == "Record 1"

    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "update", True),
            ("2020-01-01T01:00:00", "attach", False),
            (None, "attach", False),
        ],
    )
    @pytest.mark.parametrize("library, collection", [("nypl", "RL")])
    def test_review_matches_cat_rl_vendor_record(
        self, full_bib, date, action, updated, nypl_data, stub_matcher
    ):
        nypl_data["varFields"] = [
            {
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"content": "Bar", "tag": "a"}],
            }
        ]
        nypl_data["updatedDate"] = date
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
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

    @pytest.mark.parametrize(
        "date, action",
        [
            ("20250101010000.0", "update"),
            ("20200101010000.0", "attach"),
            (None, "attach"),
        ],
    )
    @pytest.mark.parametrize("library, collection", [("bpl", None)])
    def test_review_matches_cat_bpl_vendor_record(
        self, full_bib, date, action, stub_matcher
    ):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        result = stub_matcher.review_matches(full_bib, matches=[data])
        assert result.target_bib_id == "34567"
        assert result.action == action
        assert result.call_number_match is True

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_matches_nypl_mixed(self, full_bib, nypl_data, stub_matcher):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
        ]
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert len(result.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_matches_nypl_mixed_call_number(
        self, full_bib, nypl_data, stub_matcher
    ):
        nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Foo", "tag": "a"}]},
            {
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"content": "Foo", "tag": "a"}],
            },
        ]
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert len(result.mixed) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_review_matches_nypl_no_collection(self, full_bib, nypl_data, stub_matcher):
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert len(result.mixed) == 0
        assert len(result.duplicate_records) == 0
        assert result.target_bib_id is None
        assert len(result.other) == 1

    @pytest.mark.parametrize(
        "library, collection, location",
        [
            ("nypl", "RL", "myd"),
            ("nypl", "RL", "xxx"),
            ("nypl", "RL", "lsx"),
            ("nypl", "RL", "scx"),
            ("nypl", "RL", "max"),
            ("nypl", "BL", "zzzzz"),
            ("nypl", "BL", "myj"),
            ("nypl", "BL", "maj"),
            ("nypl", "BL", "agj"),
        ],
    )
    def test_review_matches_nypl_locations(
        self, full_bib, nypl_data, location, stub_matcher
    ):
        nypl_data["locations"] = [{"code": location, "name": "Foo"}]
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert len(result.mixed) == 0

    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "update", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    @pytest.mark.parametrize("library, collection", [("nypl", "BL")])
    def test_review_matches_cat_bl_no_call_no_match_vendor_source(
        self, full_bib, date, action, updated, nypl_data, stub_matcher
    ):
        nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Baz", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
        ]
        nypl_data["updatedDate"] = date
        result = stub_matcher.review_matches(full_bib, matches=[nypl_data])
        assert result.target_bib_id == "12345"
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

    @pytest.mark.parametrize("library, collection", [("bpl", None)])
    def test_review_matches_cat_bpl_no_call_no(
        self, full_bib, sierra_response, stub_matcher
    ):
        sierra_response = {
            k: v for k, v in sierra_response.items() if k != "call_number"
        }
        result = stub_matcher.review_matches(full_bib, matches=[sierra_response])
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        assert result.target_call_no is None

    @pytest.mark.parametrize("library, collection", [("bpl", None)])
    def test_review_matches_cat_bpl_no_results_midwest(self, full_bib, stub_matcher):
        full_bib.vendor = "Midwest DVD"
        result = stub_matcher.review_matches(full_bib, matches=[])
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "attach"
        assert result.call_number_match is True

    def test_bpl_sierra_response(self):
        response = sierra_responses.BPLSolrResponse(
            data={
                "call_number": "Foo",
                "id": "12345",
                "isbn": ["9781234567890"],
                "sm_bib_varfields": ["005 || 20200101000001.0", "024 || {{a}} 12345"],
                "sm_item_data": ['{"barcode": "33333123456789"}'],
                "ss_marc_tag_001": "ocn123456789",
                "ss_marc_tag_003": "OCoLC",
                "ss_marc_tag_005": "20000101010000.0",
                "title": "Record 1",
            }
        )
        assert response.barcodes == ["33333123456789"]
        assert response.branch_call_number == "Foo"
        assert response.cat_source == "inhouse"
        assert response.collection == "NONE"
        assert response.control_number == "ocn123456789"
        assert response.isbn == ["9781234567890"]
        assert response.oclc_number == ["ocn123456789"]
        assert response.research_call_number == []
        assert response.upc == ["12345"]
        assert response.update_date == "20000101010000.0"
        assert response.update_datetime == datetime.datetime(2000, 1, 1, 1)
        assert response.var_fields == [
            {"marc_tag": "024", "subfields": [{"tag": "a", "content": "12345"}]}
        ]

    @pytest.mark.parametrize("collection", ["BL", "RL"])
    def test_nypl_sierra_response(self, collection):
        response = sierra_responses.NYPLPlatformResponse(
            data={
                "id": "12345",
                "title": "Record 1",
                "updatedDate": "2020-01-01T01:00:00",
                "varFields": [
                    {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
                    {
                        "marcTag": "910",
                        "subfields": [{"content": collection, "tag": "a"}],
                    },
                ],
                "locations": [
                    {"code": "a", "name": "library"},
                    {"code": "123", "name": "library"},
                ],
            }
        )
        assert response.barcodes == []
        assert response.branch_call_number is None
        assert response.cat_source == "inhouse"
        assert response.collection == collection
        assert response.control_number is None
        assert response.isbn == []
        assert response.oclc_number == []
        assert response.research_call_number == []
        assert response.upc == []
        assert response.update_date == "2020-01-01T01:00:00"
        assert response.update_datetime == datetime.datetime(2020, 1, 1, 1)
        assert response.var_fields == [
            {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]},
        ]
