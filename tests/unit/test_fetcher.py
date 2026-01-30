import os

import pytest
import yaml

from overload_web.bib_records.domain_models import sierra_responses
from overload_web.bib_records.infrastructure import clients


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


class TestSierraBibFetcher:
    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id(self, match, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        bibs = fetcher.get_bibs_by_id(value="123456789", key=match)
        assert bibs[0].bib_id == "123456789"
        assert isinstance(fetcher.session, clients.SierraSessionProtocol)
        assert "Querying Sierra " in caplog.text

    def test_get_bibs_by_id_invalid_matchpoint(self, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        with pytest.raises(ValueError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="bar")
        assert "Unsupported query matchpoint: 'bar'" in caplog.text
        assert "Invalid matchpoint: 'bar'. Available matchpoints are:" in str(exc.value)

    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number", "issn"])
    def test_get_bibs_by_id_no_value_passed(self, match, mock_session, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_session)
        bibs = fetcher.get_bibs_by_id(value=None, key=match)
        assert bibs == []
        assert f"Skipping Sierra query on {match} with missing value." in caplog.text

    def test_get_bibs_by_id_nypl_error(self, mock_nypl_session_error, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_nypl_session_error)
        with pytest.raises(clients.BookopsPlatformError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsPlatformError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_bpl_error(self, mock_bpl_session_error, caplog):
        fetcher = clients.SierraBibFetcher(session=mock_bpl_session_error)
        with pytest.raises(clients.BookopsSolrError):
            fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert "BookopsSolrError while running Sierra queries." in caplog.text

    def test_get_bibs_by_id_nypl_issn(self, mock_session):
        fetcher = clients.SierraBibFetcher(session=clients.NYPLPlatformSession())
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in NYPL Platform" in str(exc.value)

    def test_get_bibs_by_id_bpl_issn(self, mock_session):
        fetcher = clients.SierraBibFetcher(session=clients.BPLSolrSession())
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented in BPL Solr" in str(exc.value)


class TestFetcherFactory:
    @pytest.mark.parametrize(
        "library,session_type",
        [("bpl", "BPLSolrSession"), ("nypl", "NYPLPlatformSession")],
    )
    @pytest.mark.parametrize("match", ["bib_id", "upc", "isbn", "oclc_number"])
    def test_fetcher_factory(self, library, session_type, mock_session, match, caplog):
        fetcher = clients.FetcherFactory().make(library=library)
        fetcher.get_bibs_by_id(value="123456789", key=match)
        assert len(caplog.records) == 2
        assert f"Querying Sierra with {session_type}" in caplog.records[0].msg
        assert fetcher.session.__class__.__name__ == session_type

    def test_fetcher_factory_nypl_auth_error(self, mock_nypl_session_error):
        with pytest.raises(clients.BookopsPlatformError) as exc:
            clients.FetcherFactory().make(library="nypl")
        assert "Trouble connecting: " in str(exc.value)

    def test_fetcher_factory_invalid_library(self):
        with pytest.raises(ValueError) as exc:
            clients.FetcherFactory().make(library="library")
        assert str(exc.value) == "Invalid library: library. Must be 'bpl' or 'nypl'"
