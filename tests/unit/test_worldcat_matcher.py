import pytest
from bookops_worldcat.errors import BookopsWorldcatError

from overload_web.application.wc2s import oclc_matcher
from overload_web.domain.wc2s import worldcat
from overload_web.infrastructure import oclc


@pytest.fixture
def stub_source_data(library, collection):
    return worldcat.SourceData(
        library=library,
        collection=collection,
        id="9781234567890",
        id_type=worldcat.IdType.ISBN,
        material_type=worldcat.MaterialType.PRINT,
        record_level="2",
        action=worldcat.Action.CATALOG,
    )


class TestWorldcatFetcher:
    @pytest.mark.parametrize(
        "library, index, cat_agency",
        [
            ("bpl", "sn", "DLC"),
            ("bpl", "sn", None),
            ("bpl", "sn", "DLC"),
            ("bpl", "sn", None),
            ("bpl", "no", "DLC"),
            ("bpl", "no", None),
            ("nypl", "sn", "DLC"),
            ("nypl", "sn", None),
            ("nypl", "no", "DLC"),
            ("nypl", "no", None),
        ],
    )
    @pytest.mark.parametrize(
        "format",
        ["book-printbook", "book-largeprint", "video-dvd", "video-bluray", None],
    )
    def test_get_brief_bibs_by_id(
        self, mock_wc_session, library, index, format, cat_agency, caplog
    ):
        fetcher = oclc.WorldcatFetcher(session=oclc.OclcSession(library=library))
        payload = {
            "q": f"{index}=1",
            "inCatalogLanguage": "eng",
            "catalogSource": cat_agency,
            "itemSubType": format,
            "limit": 50,
        }
        payload = {k: v for k, v in payload.items()}
        fetcher.get_brief_bibs_by_id(params=payload)
        assert len(caplog.records) == 2
        assert "Querying WorldCat for brief bibs with query" in caplog.records[0].msg
        assert (
            "MetadataSession returned 1 record(s). Returning first 50."
            == caplog.records[1].msg
        )

    @pytest.mark.parametrize(
        "library, index", [("bpl", "sn"), ("bpl", "no"), ("nypl", "sn"), ("nypl", "no")]
    )
    def test_get_brief_bibs_by_id_error(self, mock_wc_session_error, library, index):
        fetcher = oclc.WorldcatFetcher(session=oclc.OclcSession(library=library))
        with pytest.raises(BookopsWorldcatError):
            fetcher.get_brief_bibs_by_id(
                params={
                    "q": f"{index}=1",
                    "inCatalogLanguage": "eng",
                    "catalogSource": "DLC",
                    "itemSubType": "book-printbook",
                    "limit": 50,
                }
            )

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_by_id(self, mock_wc_session, library, caplog):
        fetcher = oclc.WorldcatFetcher(session=oclc.OclcSession(library=library))
        fetcher.get_full_bib_by_id(value=1)
        assert len(caplog.records) == 1
        assert "Querying WorldCat for full MARC record for" in caplog.records[0].msg

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_by_id_error(self, mock_wc_session_error, library):
        fetcher = oclc.WorldcatFetcher(session=oclc.OclcSession(library=library))
        with pytest.raises(BookopsWorldcatError):
            fetcher.get_full_bib_by_id(value=1)

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_json_by_id(self, mock_wc_session, library, caplog):
        fetcher = oclc.WorldcatFetcher(session=oclc.OclcSession(library=library))
        fetcher.get_full_bib_json_by_id(value=1)
        assert len(caplog.records) == 1
        assert (
            "Querying WorldCat for full bib record in json for" in caplog.records[0].msg
        )

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_json_by_id_error(self, mock_wc_session_error, library):
        fetcher = oclc.WorldcatFetcher(session=oclc.OclcSession(library=library))
        with pytest.raises(BookopsWorldcatError):
            fetcher.get_full_bib_json_by_id(value=1)


@pytest.mark.parametrize(
    "library, collection", [("bpl", None), ("nypl", "RL"), ("nypl", "BL")]
)
class TestWorldcatMatcher:
    def test_match_record(self, fake_oclc_fetcher, stub_source_data):
        service = oclc_matcher.WorldcatMatcher(fetcher=fake_oclc_fetcher)
        candidates = service.match_record(stub_source_data)
        assert len(candidates) == 1
        assert candidates[0] == worldcat.UpgradeItem(
            id=stub_source_data.id,
            id_type=stub_source_data.id_type,
            status=worldcat.MatchStatus.MATCHED,
            matched_oclc="12345678",
        )

    def test_match_record_failed_user_criteria(
        self, fake_oclc_fetcher, stub_source_data
    ):
        stub_source_data.record_level = "1"
        service = oclc_matcher.WorldcatMatcher(fetcher=fake_oclc_fetcher)
        candidates = service.match_record(stub_source_data)
        assert len(candidates) == 1
        assert candidates[0] == worldcat.UpgradeItem(
            id=stub_source_data.id,
            id_type=stub_source_data.id_type,
            status=worldcat.MatchStatus.FAILED_USER_CRITERIA,
            matched_oclc="12345678",
        )

    def test_match_record_failed_global_criteria(
        self, fake_oclc_fetcher, stub_source_data
    ):
        stub_source_data.update_date = "20260101000100.0"
        stub_source_data.action = worldcat.Action.UPGRADE
        service = oclc_matcher.WorldcatMatcher(fetcher=fake_oclc_fetcher)
        candidates = service.match_record(stub_source_data)
        assert len(candidates) == 1
        assert candidates[0] == worldcat.UpgradeItem(
            id=stub_source_data.id,
            id_type=stub_source_data.id_type,
            status=worldcat.MatchStatus.FAILED_GLOBAL_CRITERIA,
            matched_oclc="12345678",
        )
