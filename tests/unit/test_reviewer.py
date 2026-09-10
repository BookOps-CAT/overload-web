import pytest

from overload_web.domain.pvf import batch, models


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def stub_bib(request):
    return models.DomainBib(
        library=request.param[0],
        collection=request.param[1],
        isbn="9781234567890",
        title="Foo",
        record_type="cat",
        binary_data=b"",
        branch_call_number="Foo",
        research_call_number=["Foo"],
        barcodes=["333331234567890"],
        update_date="20200101010000.0",
        parsed_fields=[],
    )


class TestReviewer:
    # def test_validate_preserved(self, stub_bib, caplog):
    #     batch.BarcodeValidator.validate_preserved([stub_bib], ["333331234567890"])
    #     assert len(caplog.records) == 1
    #     assert (
    #         caplog.records[0].msg == "Integrity validation: True, missing_barcodes: []"
    #     )

    def test_validate_preserved_missing_barcodes(self, stub_bib, caplog):
        batch.BarcodeValidator.validate_preserved(
            [stub_bib], ["333331234567890", "333330987654321"]
        )
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].msg
            == "Integrity validation: False, missing_barcodes: ['333330987654321']"
        )
        assert caplog.records[1].msg == "Barcodes integrity error: ['333330987654321']"
