import os

import pytest
import yaml

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
            response = session._get_bibs_by_isbn("9780316230032")
            matched_bibs = session._parse_response(response=response)
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 1
            assert isinstance(matched_bibs[0], dict)
            assert sorted(list(matched_bibs[0].keys())) == [
                "author_raw",
                "call_number",
                "created_date",
                "id",
                "isbn",
                "language",
                "material_type",
                "publishYear",
                "title",
            ]

    def test_NYPLPlatformSession_live(self):
        with sierra.NYPLPlatformSession() as session:
            response = session._get_bibs_by_isbn("9780316230032")
            matched_bibs = session._parse_response(response=response)
            assert isinstance(matched_bibs, list)
            assert len(matched_bibs) == 2
            assert isinstance(matched_bibs[0], dict)
            assert sorted(list(matched_bibs[0].keys())) == [
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
    def test_get_bibs_by_id_issn(self, library, mock_sierra_response):
        fetcher = sierra.SierraBibFetcher(library=library)
        with pytest.raises(NotImplementedError) as exc:
            fetcher.get_bibs_by_id(value="123456789", key="issn")
        assert "Search by ISSN not implemented" in str(exc.value)

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_bibs_by_id_no_response(self, library, mock_sierra_no_response):
        fetcher = sierra.SierraBibFetcher(library=library)
        bibs = fetcher.get_bibs_by_id(value="123456789", key="isbn")
        assert bibs == []
