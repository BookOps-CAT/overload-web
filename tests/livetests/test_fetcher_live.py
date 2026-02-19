import os

import pytest
import yaml

from overload_web.domain.models import sierra_responses
from overload_web.infrastructure import clients


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
        with clients.BPLSolrSession() as session:
            response = session._get_bibs_by_isbn("9781338299151")
            matched_bibs = session._parse_response(response=response)
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 2
            assert isinstance(matched_bibs[0], sierra_responses.BPLSolrResponse)
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
                "ss_publisher_name",
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
        with clients.NYPLPlatformSession() as session:
            response = session._get_bibs_by_isbn("9781338299151")
            matched_bibs = session._parse_response(response=response)
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 1
            assert isinstance(matched_bibs[0], sierra_responses.NYPLPlatformResponse)
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
        fetcher = clients.FetcherFactory().make(library=library)
        bibs = fetcher.get_bibs_by_id(value="9781338299151", key="isbn")
        assert isinstance(bibs, list)
        assert sorted(list(bibs[0].keys())) == [
            "barcodes",
            "bib_id",
            "branch_call_number",
            "cat_source",
            "collection",
            "control_number",
            "isbn",
            "library",
            "oclc_number",
            "research_call_number",
            "title",
            "upc",
            "update_date",
            "var_fields",
        ]
        assert bibs[0].title is not None
