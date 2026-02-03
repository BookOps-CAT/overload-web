import copy

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.models import bibs
from overload_web.domain.services import review


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
                subfields=[
                    Subfield(code="a", value="333331111111111"),
                ],
            )
        )
    else:
        new_bib.remove_fields("949")
        new_bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", "1"),
                subfields=[
                    Subfield(code="i", value="333331111111111"),
                ],
            )
        )
        new_bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="i", value="*b2=a;"),
                ],
            )
        )
    new_full_bib.binary_data = new_bib.as_marc()
    new_full_bib.barcodes = ["333331111111111"]
    return new_full_bib


@pytest.fixture
def stub_analysis(full_bib):
    return bibs.MatchAnalysis(
        True,
        bibs.ClassifiedCandidates([], [], []),
        full_bib.collection,
        bibs.MatchDecision(bibs.CatalogAction.INSERT, target_bib_id=full_bib.bib_id),
        full_bib.library,
        full_bib.match_identifiers(),
        full_bib.record_type,
        full_bib.vendor,
    )


class TestReviewer:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_dedupe_attach(self, full_bib, update_strategy):
        service = review.BibReviewer(context_factory=update_strategy)
        deduped_bibs = service.dedupe(
            [full_bib],
            [
                bibs.MatchAnalysis(
                    True,
                    bibs.ClassifiedCandidates([], [], []),
                    full_bib.collection,
                    bibs.MatchDecision(
                        bibs.CatalogAction.ATTACH, target_bib_id=full_bib.bib_id
                    ),
                    full_bib.library,
                    full_bib.match_identifiers(),
                    full_bib.record_type,
                    full_bib.vendor,
                ),
            ],
        )
        assert len(deduped_bibs["DUP"]) == 1
        assert len(deduped_bibs["NEW"]) == 0
        assert len(deduped_bibs["DEDUPED"]) == 0

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_dedupe_insert(self, full_bib, update_strategy, stub_analysis):
        service = review.BibReviewer(context_factory=update_strategy)
        deduped_bibs = service.dedupe([full_bib], [stub_analysis])
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["NEW"]) == 1
        assert len(deduped_bibs["DEDUPED"]) == 0

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("bpl", "NONE", "cat")],
    )
    def test_dedupe_deduped_bpl(
        self, library, full_bib, full_bib_add_barcodes, update_strategy, stub_analysis
    ):
        service = review.BibReviewer(context_factory=update_strategy)
        deduped_bibs = service.dedupe(
            [full_bib, full_bib_add_barcodes],
            [stub_analysis, stub_analysis],
        )
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["NEW"]) == 2
        assert len(deduped_bibs["DEDUPED"]) == 1
        deduped = Bib(deduped_bibs["DEDUPED"][0].binary_data, library=library)
        assert len(deduped.get_fields("960")) == 2
        assert [i.value() for i in deduped.get_fields("960")] == [
            "333331234567890",
            "333331111111111",
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat")],
    )
    def test_dedupe_deduped_nypl(
        self, library, full_bib, full_bib_add_barcodes, update_strategy, stub_analysis
    ):
        service = review.BibReviewer(context_factory=update_strategy)
        deduped_bibs = service.dedupe(
            [full_bib, full_bib_add_barcodes], [stub_analysis, stub_analysis]
        )
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["NEW"]) == 2
        assert len(deduped_bibs["DEDUPED"]) == 1
        deduped = Bib(deduped_bibs["DEDUPED"][0].binary_data, library=library)
        assert len(deduped.get_fields("949")) == 2
        assert [i.value() for i in deduped.get_fields("949")] == [
            "333331234567890",
            "333331111111111",
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_dedupe_other_recs(
        self, full_bib, full_bib_add_barcodes, stub_analysis, update_strategy
    ):
        other_rec = copy.deepcopy(full_bib)
        other_rec.control_number = "123456789"
        service = review.BibReviewer(context_factory=update_strategy)
        analysis = bibs.MatchAnalysis(
            True,
            bibs.ClassifiedCandidates([], [], []),
            full_bib.collection,
            bibs.MatchDecision(bibs.CatalogAction.INSERT, target_bib_id=None),
            full_bib.library,
            full_bib.match_identifiers(),
            full_bib.record_type,
            full_bib.vendor,
        )
        deduped_bibs = service.dedupe(
            [full_bib, full_bib_add_barcodes, other_rec],
            [stub_analysis, stub_analysis, analysis],
        )
        assert len(deduped_bibs["DUP"]) == 0
        assert len(deduped_bibs["NEW"]) == 3
        assert len(deduped_bibs["DEDUPED"]) == 3

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

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_dedupe_and_validate_cat(self, full_bib, update_strategy):
        service = review.BibReviewer(context_factory=update_strategy)
        decision = bibs.MatchDecision(
            bibs.CatalogAction.ATTACH, target_bib_id=full_bib.bib_id
        )
        deduped_bibs = service.dedupe_and_validate(
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
            ["333331234567890"],
        )
        assert len(deduped_bibs["DUP"]) == 1
        assert len(deduped_bibs["NEW"]) == 0
        assert len(deduped_bibs["DEDUPED"]) == 0
