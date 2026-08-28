import pytest
from bookops_worldcat.errors import BookopsWorldcatError

from overload_web.infrastructure import oclc


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
        fetcher = oclc.WorldcatFetcher(library=library)
        fetcher.get_brief_bibs_by_id(
            index=index, value=1, format=format, cat_agency=cat_agency
        )
        assert len(caplog.records) == 3
        assert "Querying WorldCat for brief bibs with query" in caplog.records[0].msg
        assert "MetadataSession response code: 200." == caplog.records[1].msg
        assert (
            "MetadataSession returned 1 record(s). Returning first 50."
            == caplog.records[2].msg
        )

    @pytest.mark.parametrize(
        "library, index", [("bpl", "sn"), ("bpl", "no"), ("nypl", "sn"), ("nypl", "no")]
    )
    def test_get_brief_bibs_by_id_error(self, mock_wc_session_error, library, index):
        fetcher = oclc.WorldcatFetcher(library=library)
        with pytest.raises(BookopsWorldcatError):
            fetcher.get_brief_bibs_by_id(
                index=index, value=1, format="book-printbook", cat_agency="DLC"
            )

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_by_id(self, mock_wc_session, library, caplog):
        fetcher = oclc.WorldcatFetcher(library=library)
        fetcher.get_full_bib_by_id(value=1)
        assert len(caplog.records) == 1
        assert "Querying WorldCat for full MARC record for" in caplog.records[0].msg

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_by_id_error(self, mock_wc_session_error, library):
        fetcher = oclc.WorldcatFetcher(library=library)
        with pytest.raises(BookopsWorldcatError):
            fetcher.get_full_bib_by_id(value=1)

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_json_by_id(self, mock_wc_session, library, caplog):
        fetcher = oclc.WorldcatFetcher(library=library)
        fetcher.get_full_bib_json_by_id(value=1)
        assert len(caplog.records) == 1
        assert (
            "Querying WorldCat for full bib record in json for" in caplog.records[0].msg
        )

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_full_bib_json_by_id_error(self, mock_wc_session_error, library):
        fetcher = oclc.WorldcatFetcher(library=library)
        with pytest.raises(BookopsWorldcatError):
            fetcher.get_full_bib_json_by_id(value=1)
