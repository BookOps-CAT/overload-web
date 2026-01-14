import pytest

from overload_web.bib_records.domain_services import review
from overload_web.bib_records.infrastructure import marc_updater


class TestReviewer:
    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_cat(
        self, full_bib, match_resolution, library, test_constants, collection, caplog
    ):
        service = review.FullLevelBibReviewer(
            handler=marc_updater.BookopsMarcUpdateHandler(
                library=library, record_type="cat", rules=test_constants
            )
        )
        deduped_bibs = service.dedupe([full_bib], [match_resolution])
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["NEW"]) == 1
        assert len(deduped_bibs["DEDUPED"]) == 0

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_validate_cat(self, full_bib, library, collection, test_constants, caplog):
        service = review.FullLevelBibReviewer(
            handler=marc_updater.BookopsMarcUpdateHandler(
                library=library, record_type="cat", rules=test_constants
            )
        )
        service.validate({"NEW": [full_bib]}, ["333331234567890"])
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
        )

    def test_validate_cat_bpl_960_item(self, full_bpl_bib, test_constants, caplog):
        service = review.FullLevelBibReviewer(
            handler=marc_updater.BookopsMarcUpdateHandler(
                library="bpl", record_type="cat", rules=test_constants
            )
        )
        service.validate({"NEW": [full_bpl_bib]}, ["333331234567890"])
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_validate_missing_barcodes(
        self, full_bib, library, collection, test_constants, caplog
    ):
        service = review.FullLevelBibReviewer(
            handler=marc_updater.BookopsMarcUpdateHandler(
                library=library, record_type="cat", rules=test_constants
            )
        )
        service.validate({"NEW": [full_bib]}, ["333331234567890", "333330987654321"])
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == "Integrity validation: False, missing_barcodes: ['333330987654321']"
        )
        assert caplog.records[1].msg == "Barcodes integrity error: ['333330987654321']"

    def test_validate_bpl_960_item_missing_barcodes(
        self, full_bpl_bib, test_constants, caplog
    ):
        service = review.FullLevelBibReviewer(
            handler=marc_updater.BookopsMarcUpdateHandler(
                library="bpl", record_type="cat", rules=test_constants
            )
        )
        service.validate(
            {"NEW": [full_bpl_bib]}, ["333331234567890", "333330987654321"]
        )
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == "Integrity validation: False, missing_barcodes: ['333330987654321']"
        )
        assert caplog.records[1].msg == "Barcodes integrity error: ['333330987654321']"
