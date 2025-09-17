import os

import pytest
import yaml

from overload_web import errors
from overload_web.infrastructure.bibs import sierra


@pytest.fixture
def live_creds() -> None:
    with open(
        os.path.join(os.environ["USERPROFILE"], ".cred/.overload/live_creds.yaml")
    ) as cred_file:
        data = yaml.safe_load(cred_file)
        for k, v in data.items():
            os.environ[k] = v


@pytest.mark.livetest
@pytest.mark.usefixtures("live_creds")
class TestLiveSierraSession:
    def test_BPLSolrSession_live(self):
        with sierra.BPLSolrSession() as session:
            response = session._get_bibs_by_isbn("9781338299151")
            matched_bibs = session._parse_response(response=response)
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 2
            assert isinstance(matched_bibs[0], sierra.BPLSolrResponse)
            assert sorted(list(response.json()["response"]["docs"][0].keys())) == [
                "_version_",
                "additional_contributor",
                "author",
                "author_alt",
                "author_raw",
                "available",
                "bs_all_lib_use_only",
                "bs_on_order",
                "call_number",
                "collection",
                "created_date",
                "deleted",
                "fiction_status",
                "fs_call_number",
                "id",
                "is_available_locations",
                "is_book_discussion",
                "is_copies",
                "is_copies_non_deleted",
                "is_copies_sort",
                "is_holds",
                "isbn",
                "language",
                "material_type",
                "opac_label",
                "popularity",
                "publishYear",
                "publisher",
                "sm_bib_varfields",
                "sm_item_data",
                "ss_author_autocomplete",
                "ss_biblevel",
                "ss_grouping",
                "ss_marc_tag_001",
                "ss_marc_tag_003",
                "ss_marc_tag_005",
                "ss_title_autocomplete",
                "ss_type",
                "subjects",
                "summary",
                "suppressed",
                "target_age",
                "timestamp",
                "title",
                "tm_content",
                "tm_primary_title",
                "tm_subject_search",
            ]
            assert sorted(list(matched_bibs[0].__dict__.keys())) == [
                "_data",
                "bib_id",
                "library",
                "title",
            ]
            assert matched_bibs[0].title is not None

    def test_NYPLPlatformSession_live(self):
        with sierra.NYPLPlatformSession() as session:
            response = session._get_bibs_by_isbn("9781338299151")
            matched_bibs = session._parse_response(response=response)
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 1
            assert isinstance(matched_bibs[0], sierra.NYPLPlatformResponse)
            assert sorted(list(response.json()["data"][0].keys())) == [
                "author",
                "bibLevel",
                "catalogDate",
                "controlNumber",
                "country",
                "createdDate",
                "deleted",
                "deletedDate",
                "fixedFields",
                "id",
                "lang",
                "locations",
                "materialType",
                "normAuthor",
                "normTitle",
                "nyplSource",
                "nyplType",
                "publishYear",
                "standardNumbers",
                "suppressed",
                "title",
                "updatedDate",
                "varFields",
            ]
            assert matched_bibs[0].title is not None

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_SierraBibFetcher_live(self, library):
        fetcher = sierra.SierraBibFetcher(library=library)
        bibs = fetcher.get_bibs_by_id(value="9781338299151", key="isbn")
        assert isinstance(bibs, list)
        assert sorted(list(bibs[0].keys())) == [
            "barcodes",
            "bib_id",
            "branch_call_no",
            "cat_source",
            "collection",
            "control_number",
            "isbn",
            "library",
            "oclc_number",
            "research_call_no",
            "title",
            "upc",
            "update_date",
            "var_fields",
        ]
        assert bibs[0]["title"] is not None


class TestSierraSessions:
    @pytest.mark.parametrize(
        "library,session_type",
        [("bpl", sierra.BPLSolrSession), ("nypl", sierra.NYPLPlatformSession)],
    )
    @pytest.mark.parametrize("matchpoint", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_by_id(
        self, library, session_type, matchpoint, mock_sierra_response
    ):
        fetcher = sierra.SierraBibFetcher(library=library)
        bibs = fetcher.get_bibs_by_id(value="123456789", key=matchpoint)
        assert bibs[0]["bib_id"] == "123456789"
        assert isinstance(fetcher.session, session_type)

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_bibs_by_id_issn(self, library, mock_sierra_response, caplog):
        fetcher = sierra.SierraBibFetcher(library=library)
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented" in str(exc.value)
        assert "Invalid matchpoint: 'issn'. Available matchpoints are: isbn, upc, oclc_number, bib_id"

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_bibs_by_id_no_response(self, library, mock_sierra_no_response):
        fetcher = sierra.SierraBibFetcher(library=library)
        bibs = fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert bibs == []

    @pytest.mark.parametrize(
        "library,session_type",
        [("bpl", "BPLSolrSession"), ("nypl", "NYPLPlatformSession")],
    )
    @pytest.mark.parametrize("matchpoint", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_get_bibs_by_id_logging(
        self, library, session_type, matchpoint, mock_sierra_response, caplog
    ):
        fetcher = sierra.SierraBibFetcher(library=library)
        fetcher.get_bibs_by_id(value="123456789", key=matchpoint)
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == f"Querying Sierra with {session_type} on {matchpoint} with value: 123456789."
        )
        assert caplog.records[1].msg == "Sierra Session response code: 200."

    @pytest.mark.parametrize(
        "library,error_type",
        [("bpl", "BookopsSolrError"), ("nypl", "BookopsPlatformError")],
    )
    def test_get_bibs_by_id_error(self, library, mock_sierra_error, caplog, error_type):
        fetcher = sierra.SierraBibFetcher(library=library)
        with pytest.raises(errors.OverloadError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "Connection error: " in str(exc.value)
        assert f"{error_type} while running Sierra queries." in caplog.text

    @pytest.mark.parametrize("library", ["nypl"])
    def test_get_bibs_by_id_nypl_auth_error(self, library, mock_sierra_nypl_auth_error):
        with pytest.raises(errors.OverloadError) as exc:
            sierra.SierraBibFetcher(library=library)
        assert "Trouble connecting: " in str(exc.value)
