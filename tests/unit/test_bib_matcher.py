from contextlib import nullcontext as does_not_raise

import pytest

from overload_web.application.pvf import match_service
from overload_web.domain.pvf import matching, models
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
        "updatedDate": "2000-01-01T01:00:00",
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
    "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
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


@pytest.mark.parametrize(
    "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
)
class TestSelectionMatchAnalyzer:
    ANALYZER = matching.SelectionMatchAnalyzer()

    def test_classify_matches_duplicates(self, full_bib, sierra_response):
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[sierra_response, sierra_response]
        )
        assert classified.duplicates == ["12345", "12345"]

    def test_classify_matches_unknown_library(self, full_bib, sierra_response):
        full_bib.library = "FOO"
        with pytest.raises(ValueError) as exc:
            self.ANALYZER.classify_matches(record=full_bib, matches=[sierra_response])
        assert str(exc.value) == "Unknown library: FOO. Cannot classify matches."

    def test_analyze(self, sel_bib, sierra_response):
        candidates = self.ANALYZER.classify_matches(
            record=sel_bib, matches=[sierra_response]
        )
        result = self.ANALYZER.analyze(record=sel_bib, candidates=candidates)
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

    def test_analyze_no_matches(self, sel_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.ANALYZER.analyze(record=sel_bib, candidates=candidates)
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

    def test_analyze_no_call_no(self, sel_bib, collection, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]}
        ]
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=sel_bib, candidates=candidates)
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
    ANALYZER = matching.AcquisitionsMatchAnalyzer()

    def test_action_attr(self, acq_bib):
        with pytest.raises(AttributeError) as exc:
            acq_bib.action
        assert str(exc.value) == "CatalogAction has not been assigned to the DomainBib"

    def test_analyze(self, acq_bib, sierra_response):
        candidates = self.ANALYZER.classify_matches(
            record=acq_bib, matches=[sierra_response]
        )
        result = self.ANALYZER.analyze(record=acq_bib, candidates=candidates)
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
        response = sierra_responses.NYPLPlatformResponse(sierra_response)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=acq_bib, candidates=candidates)
        assert result.resource_id == "123456789"
        assert result.call_number == "Foo"

    def test_resource_id_none(self, acq_bib, sierra_response):
        acq_bib.isbn = None
        response = sierra_responses.NYPLPlatformResponse(sierra_response)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=acq_bib, candidates=candidates)
        assert result.resource_id is None
        assert acq_bib.control_number is None
        assert acq_bib.isbn is None
        assert acq_bib.oclc_number is None
        assert acq_bib.upc is None


@pytest.mark.parametrize("library, collection", [("nypl", "BL")])
class TestNYPLCatBranchMatchAnalyzer:
    ANALYZER = matching.NYPLCatBranchMatchAnalyzer()

    @pytest.mark.parametrize("location", ["zzzzz", "myj", "maj", "agj"])
    def test_classify_matches_nypl_bl_locations(self, full_bib, nypl_data, location):
        nypl_data["locations"] = [{"code": location, "name": "Foo"}]
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.matched) == 1
        assert len(classified.mixed) == 0

    def test_classify_matches_nypl_mixed(self, full_bib, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
        ]
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.mixed) == 1

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
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.mixed) == 1

    def test_classify_matches_nypl_no_collection(self, full_bib, nypl_data):
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.mixed) == 0
        assert len(classified.duplicates) == 0
        assert len(classified.matched) == 0
        assert len(classified.other) == 1

    def test_analyze(self, full_bib, sierra_response):
        response = sierra_responses.NYPLPlatformResponse(sierra_response)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
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

    def test_analyze_no_matches(self, full_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
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

    @pytest.mark.parametrize(
        "date, action, updated",
        [
            ("2025-01-01T01:00:00", "update", True),
            ("2020-01-01T01:00:00", "attach", False),
        ],
    )
    def test_analyze_no_call_number_match_vendor_source(
        self, full_bib, date, action, updated, nypl_data
    ):
        nypl_data["varFields"] = [
            {"marcTag": "091", "subfields": [{"content": "Baz", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
        ]
        nypl_data["updatedDate"] = date
        response = sierra_responses.NYPLPlatformResponse(nypl_data)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
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
    ANALYZER = matching.NYPLCatResearchMatchAnalyzer()

    @pytest.mark.parametrize("location", ["myd", "xxx", "lsx", "scx", "max"])
    def test_classify_matches_nypl_rl_locations(self, full_bib, nypl_data, location):
        nypl_data["locations"] = [{"code": location, "name": "Foo"}]
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.matched) == 1
        assert len(classified.mixed) == 0

    def test_classify_matches_nypl_mixed(self, full_bib, nypl_data):
        nypl_data["varFields"] = [
            {"marcTag": "910", "subfields": [{"content": "BL", "tag": "a"}]},
            {"marcTag": "910", "subfields": [{"content": "RL", "tag": "a"}]},
        ]
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.mixed) == 1

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
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.mixed) == 1

    def test_classify_matches_nypl_no_collection(self, full_bib, nypl_data):
        classified = self.ANALYZER.classify_matches(
            record=full_bib, matches=[nypl_data]
        )
        assert len(classified.mixed) == 0
        assert len(classified.duplicates) == 0
        assert len(classified.matched) == 0
        assert len(classified.other) == 1

    def test_analyze(self, full_bib, sierra_response):
        response = sierra_responses.NYPLPlatformResponse(sierra_response)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
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

    def test_analyze_no_results(self, full_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
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
            ("2025-01-01T01:00:00", "update", True),
            ("2020-01-01T01:00:00", "attach", False),
            (None, "attach", False),
        ],
    )
    def test_analyze_vendor_record(self, full_bib, date, action, updated, nypl_data):
        nypl_data["varFields"] = [
            {
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"content": "Bar", "tag": "a"}],
            }
        ]
        nypl_data["updatedDate"] = date
        response = sierra_responses.NYPLPlatformResponse(data=nypl_data)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
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

    def test_analyze_no_call_no(self, full_bib, sierra_response):
        sierra_response["varFields"] = [
            i for i in sierra_response["varFields"] if i["marcTag"] != "852"
        ]
        response = sierra_responses.NYPLPlatformResponse(data=sierra_response)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.action == "update"
        assert result.mixed == []
        assert result.other == []
        assert result.duplicate_records == []
        assert result.resource_id == "9781234567890"
        assert result.call_number == "Foo"
        assert result.call_number_match is False
        assert result.updated_by_vendor is False
        assert result.target_call_no is None
        assert result.target_title == "Record 1"


@pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
class TestBPLCatMatchAnalyzer:
    ANALYZER = matching.BPLCatMatchAnalyzer()

    def test_analyze(self, full_bib, sierra_response):
        response = sierra_responses.BPLSolrResponse(data=sierra_response)
        candidates = matching.ClassifiedCandidates(
            matched=[response], mixed=[], other=[]
        )
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
        assert full_bib.bib_id is None
        assert result.target_bib_id == "12345"
        assert result.duplicate_records == []
        assert result.call_number == "Foo"
        # test that the BPL response is parsed correctly
        assert response.barcodes == ["33333123456789"]
        assert response.cat_source == "inhouse"
        assert response.control_number == "ocn123456789"
        assert response.isbn == ["9781234567890"]
        assert sorted(response.oclc_number) == sorted(["ocn123456789"])
        assert response.research_call_number == []
        assert sorted(response.upc) == sorted(["12345"])
        assert result.call_number_match is True

    def test_analyze_no_results(self, full_bib):
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "insert"
        assert result.call_number_match is True

    def test_analyze_no_results_midwest(self, full_bib):
        full_bib.vendor = "Midwest DVD"
        candidates = matching.ClassifiedCandidates([], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
        assert full_bib.bib_id is None
        assert result.target_bib_id is None
        assert result.action == "attach"
        assert result.call_number_match is True

    @pytest.mark.parametrize(
        "date, action",
        [
            ("20250101010000.0", "update"),
            ("20200101010000.0", "attach"),
            (None, "attach"),
        ],
    )
    def test_analyze_vendor_record(self, full_bib, date, action):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": date,
            "call_number": "Foo",
        }
        response = sierra_responses.BPLSolrResponse(data=data)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
        assert result.target_bib_id == "34567"
        assert response.cat_source == "vendor"
        assert result.action == action
        assert result.call_number_match is True

    def test_analyze_no_call_no(self, full_bib):
        data = {
            "id": "34567",
            "title": "Record 3",
            "ss_marc_tag_005": "20250101010000.0",
        }
        response = sierra_responses.BPLSolrResponse(data=data)
        candidates = matching.ClassifiedCandidates([response], [], [])
        result = self.ANALYZER.analyze(record=full_bib, candidates=candidates)
        assert result.target_bib_id == "34567"
        assert result.action == "update"
        assert result.call_number_match is False
