import copy

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain_services import updater
from overload_web.bib_records.infrastructure.marc import update_strategy
from overload_web.errors import OverloadError


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestUpdater:
    def test_update_cat(self, stub_full_bib):
        original_bib = Bib(
            copy.deepcopy(stub_full_bib.binary_data), library=str(stub_full_bib.library)
        )
        stub_full_bib.bib_id = "12345"
        stub_service = updater.BibRecordUpdater(
            strategy=update_strategy.MarcUpdaterFactory().make(record_type="cat")
        )
        updated_bibs = stub_service.update([stub_full_bib])
        updated_bib = Bib(
            updated_bibs[0].binary_data, library=str(updated_bibs[0].library)
        )
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("907")) == 1

    def test_update_cat_no_vendor_index(self, stub_order_bib):
        stub_service = updater.BibRecordUpdater(
            strategy=update_strategy.MarcUpdaterFactory().make(record_type="cat")
        )
        with pytest.raises(OverloadError) as exc:
            stub_service.update([stub_order_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_update_cat_vendor_updates(self, make_full_bib, library):
        dto = make_full_bib(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(Bib(dto.binary_data, library=library))
        stub_service = updater.BibRecordUpdater(
            strategy=update_strategy.MarcUpdaterFactory().make(record_type="cat")
        )
        updated_bibs = stub_service.update([dto])
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    def test_update_acq(self, stub_order_bib, template_data):
        original_orders = copy.deepcopy(stub_order_bib.orders)
        stub_service = updater.BibRecordUpdater(
            strategy=update_strategy.MarcUpdaterFactory().make(record_type="acq")
        )
        updated_bibs = stub_service.update(
            [stub_order_bib], template_data=template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    def test_update_sel(self, stub_order_bib, template_data):
        original_orders = copy.deepcopy(stub_order_bib.orders)
        stub_service = updater.BibRecordUpdater(
            strategy=update_strategy.MarcUpdaterFactory().make(record_type="sel")
        )
        updated_bibs = stub_service.update(
            [stub_order_bib], template_data=template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "record_type",
        ["acq", "sel"],
    )
    def test_update_acq_sel_no_template(self, stub_order_bib, record_type):
        stub_service = updater.BibRecordUpdater(
            strategy=update_strategy.MarcUpdaterFactory().make(record_type=record_type)
        )
        with pytest.raises(OverloadError) as exc:
            stub_service.update([stub_order_bib])
        assert (
            str(exc.value)
            == "Order template required for acquisition or selection workflow."
        )
