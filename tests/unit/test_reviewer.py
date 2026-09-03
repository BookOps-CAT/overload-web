import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.application.pvf import marc
from overload_web.domain.pvf import batch, models
from overload_web.infrastructure import marc_engine


@pytest.fixture
def full_bib_add_barcodes(full_bib, library):
    new_full_bib = copy.deepcopy(full_bib)
    new_bib = Bib(new_full_bib.binary_data, library=library)
    if library == "bpl":
        new_bib.remove_fields("960")
        new_bib.add_field(
            Field(
                tag="960",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="333331111111111")],
            )
        )
    else:
        new_bib.remove_fields("949")
        new_bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", "1"),
                subfields=[Subfield(code="i", value="333331111111111")],
            )
        )
        new_bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="i", value="*b2=a;")],
            )
        )
    new_full_bib.binary_data = new_bib.as_marc()
    new_full_bib.barcodes = ["333331111111111"]
    return new_full_bib


class TestReviewer:
    ENGINE = marc_engine.MarcUpdateEngine()

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_attach(self, full_bib):
        full_bib.action = models.CatalogAction.ATTACH
        deduped_bibs = marc.BibDeduplicator.deduplicate(
            records=[full_bib], engine=self.ENGINE
        )
        assert len(deduped_bibs["NEW"]) == 1
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["DEDUPED"]) == 0

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_insert(self, full_bib):
        full_bib.action = models.CatalogAction.INSERT
        deduped_bibs = marc.BibDeduplicator.deduplicate(
            records=[full_bib], engine=self.ENGINE
        )
        assert len(deduped_bibs["NEW"]) == 0
        assert len(deduped_bibs["DUP"]) == 1
        assert len(deduped_bibs["DEDUPED"]) == 0

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_dedupe_bpl(self, library, full_bib, full_bib_add_barcodes):
        full_bib.action = models.CatalogAction.INSERT
        full_bib_add_barcodes.action = models.CatalogAction.INSERT
        deduped_bibs = marc.BibDeduplicator.deduplicate(
            records=[full_bib, full_bib_add_barcodes], engine=self.ENGINE
        )
        assert len(deduped_bibs["NEW"]) == 0
        assert len(deduped_bibs["DUP"]) == 2
        assert len(deduped_bibs["DEDUPED"]) == 1
        deduped = Bib(deduped_bibs["DEDUPED"][0].binary_data, library=library)
        assert len(deduped.get_fields("960")) == 2
        assert [i.value() for i in deduped.get_fields("960")] == [
            "333331234567890",
            "333331111111111",
        ]

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_dedupe_deduped_nypl(self, library, full_bib, full_bib_add_barcodes):
        full_bib.action = models.CatalogAction.INSERT
        full_bib_add_barcodes.action = models.CatalogAction.INSERT
        deduped_bibs = marc.BibDeduplicator.deduplicate(
            records=[full_bib, full_bib_add_barcodes], engine=self.ENGINE
        )
        assert len(deduped_bibs["NEW"]) == 0
        assert len(deduped_bibs["DUP"]) == 2
        assert len(deduped_bibs["DEDUPED"]) == 1
        deduped = Bib(deduped_bibs["DEDUPED"][0].binary_data, library=library)
        assert len(deduped.get_fields("949")) == 2
        assert [i.value() for i in deduped.get_fields("949")] == [
            "333331234567890",
            "333331111111111",
        ]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_dedupe_other_recs(self, full_bib, full_bib_add_barcodes):
        other_rec = copy.deepcopy(full_bib)
        other_rec.control_number = "123456789"
        other_rec.action = models.CatalogAction.INSERT
        full_bib.action = models.CatalogAction.INSERT
        full_bib_add_barcodes.action = models.CatalogAction.INSERT
        deduped_bibs = marc.BibDeduplicator.deduplicate(
            records=[full_bib, full_bib_add_barcodes, other_rec], engine=self.ENGINE
        )
        assert len(deduped_bibs["NEW"]) == 0
        assert len(deduped_bibs["DUP"]) == 3
        assert len(deduped_bibs["DEDUPED"]) == 3

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
