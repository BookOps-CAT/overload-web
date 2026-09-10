import pytest

from overload_web.domain.pvf import batch


class TestReviewer:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_validate_preserved(self, full_bib, caplog, record_type):
        batch.BarcodeValidator.validate_preserved([full_bib], ["333331234567890"])
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
        )

    @pytest.mark.parametrize(
        "library, collection, record_type", [("bpl", "NONE", "cat")]
    )
    def test_validate_preserved_bpl_960_item(
        self, full_bib, caplog, collection, record_type
    ):
        batch.BarcodeValidator.validate_preserved([full_bib], ["333331234567890"])
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
        )

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_validate_preserved_missing_barcodes(
        self, full_bib, caplog, collection, record_type
    ):
        batch.BarcodeValidator.validate_preserved(
            [full_bib], ["333331234567890", "333330987654321"]
        )
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == "Integrity validation: False, missing_barcodes: ['333330987654321']"
        )
        assert caplog.records[1].msg == "Barcodes integrity error: ['333330987654321']"
