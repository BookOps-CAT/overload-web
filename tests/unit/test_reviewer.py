import pytest

from overload_web.bib_records.domain_models import bibs
from overload_web.bib_records.domain_services import review


class TestReviewer:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_dedupe_cat(self, full_bib, update_strategy):
        service = review.BibReviewer(context_factory=update_strategy)
        decision = bibs.MatchDecision(
            bibs.CatalogAction.ATTACH, target_bib_id=full_bib.bib_id
        )
        deduped_bibs = service.dedupe(
            [full_bib],
            [
                bibs.MatchAnalysis(
                    True,
                    bibs.ClassifiedCandidates([], [], []),
                    full_bib.collection,
                    decision,
                    full_bib.library,
                    full_bib.match_identifiers(),
                    full_bib.record_type,
                    full_bib.vendor,
                ),
            ],
        )
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["NEW"]) == 1
        assert len(deduped_bibs["DEDUPED"]) == 0

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_validate_cat(self, full_bib, update_strategy, caplog):
        service = review.BibReviewer(context_factory=update_strategy)
        service.validate({"NEW": [full_bib]}, ["333331234567890"])
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
        )

    @pytest.mark.parametrize(
        "library, collection, record_type", [("bpl", "NONE", "cat")]
    )
    def test_validate_cat_bpl_960_item(
        self, full_bib, update_strategy, caplog, collection
    ):
        service = review.BibReviewer(context_factory=update_strategy)
        service.validate({"NEW": [full_bib]}, ["333331234567890"])
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_validate_missing_barcodes(
        self, full_bib, update_strategy, caplog, collection
    ):
        service = review.BibReviewer(context_factory=update_strategy)
        service.validate({"NEW": [full_bib]}, ["333331234567890", "333330987654321"])
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == "Integrity validation: False, missing_barcodes: ['333330987654321']"
        )
        assert caplog.records[1].msg == "Barcodes integrity error: ['333330987654321']"

    @pytest.mark.parametrize(
        "library, collection, record_type", [("bpl", "NONE", "cat")]
    )
    def test_validate_bpl_960_item_missing_barcodes(
        self, full_bib, update_strategy, caplog, collection
    ):
        service = review.BibReviewer(context_factory=update_strategy)
        service.validate({"NEW": [full_bib]}, ["333331234567890", "333330987654321"])
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == "Integrity validation: False, missing_barcodes: ['333330987654321']"
        )
        assert caplog.records[1].msg == "Barcodes integrity error: ['333330987654321']"
