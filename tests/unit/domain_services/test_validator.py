import pytest

from overload_web.domain.pvf import services


class TestBarcodeValidator:
    VALIDATOR = services.BarcodeValidator()

    def test_validate_unique(self):
        validated = self.VALIDATOR.validate_unique(
            barcodes=[
                ["333331234567890", "333330987654321"],
                ["333331111111111", "333332222222222"],
            ]
        )
        assert sorted(validated) == sorted(
            ["333331234567890", "333330987654321", "333331111111111", "333332222222222"]
        )

    def test_validate_unique_dupes(self):
        with pytest.raises(ValueError) as exc:
            self.VALIDATOR.validate_unique(
                barcodes=[
                    ["333331234567890", "333330987654321"],
                    ["333331111111111", "333331111111111"],
                ]
            )
        assert str(exc.value) == "Duplicate barcodes found in file: ['333331111111111']"

    def test_validate_preserved(self):
        missing = self.VALIDATOR.validate_preserved(
            processed_barcodes=[
                ["333331234567890", "333330987654321"],
                ["333331111111111", "333332222222222"],
            ],
            original_barcodes=[
                "333331234567890",
                "333330987654321",
                "333331111111111",
                "333332222222222",
            ],
        )
        assert missing == []

    def test_validate_preserved_missing(self, caplog):
        caplog.set_level("DEBUG")
        missing = self.VALIDATOR.validate_preserved(
            processed_barcodes=[
                ["333331234567890", "333330987654321"],
                ["333331111111111"],
            ],
            original_barcodes=[
                "333331234567890",
                "333330987654321",
                "333331111111111",
                "333332222222222",
            ],
        )
        assert missing == ["333332222222222"]
        assert [i.msg for i in caplog.records] == [
            "Integrity validation: False, missing_barcodes: ['333332222222222']",
            "Barcodes integrity error: ['333332222222222']",
        ]
