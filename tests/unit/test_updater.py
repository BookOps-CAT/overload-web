import copy

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain_services import update
from overload_web.bib_records.infrastructure import marc_updater


class TestUpdater:
    update_handler = marc_updater.BookopsMarcUpdateHandler()

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_update_cat_bpl(self, full_bib):
        original_bib = Bib(
            copy.deepcopy(full_bib.binary_data), library=full_bib.library
        )

        full_bib.bib_id = "12345"
        service = update.FullLevelBibUpdater(
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([full_bib])
        updated_bib = Bib(updated_bibs[0].binary_data, library=updated_bibs[0].library)
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("907")) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_update_cat_nypl(self, full_bib):
        original_bib = Bib(
            copy.deepcopy(full_bib.binary_data), library=full_bib.library
        )
        full_bib.bib_id = "12345"
        service = update.FullLevelBibUpdater(
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([full_bib])
        updated_bib = Bib(updated_bibs[0].binary_data, library=updated_bibs[0].library)
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("945")) == 1

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_cat_vendor_updates(self, full_bib, library):
        full_bib.vendor = "INGRAM"
        full_bib.vendor_info = update.bibs.VendorInfo(
            name="INGRAM",
            matchpoints={"primary_matchpoint": "oclc_number"},
            bib_fields=[
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        )
        original_bib = copy.deepcopy(Bib(full_bib.binary_data, library=library))
        service = update.FullLevelBibUpdater(
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([full_bib])
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_acq(self, order_level_bib, fake_template_data, test_constants):
        order_level_bib.record_type = "acq"
        original_orders = copy.deepcopy(order_level_bib.orders)
        service = update.OrderLevelBibUpdater(
            rules=test_constants,
            update_handler=self.update_handler,
        )
        updated_bibs = service.update(
            [order_level_bib], template_data=fake_template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_sel(self, order_level_bib, fake_template_data, test_constants):
        order_level_bib.record_type = "sel"
        original_orders = copy.deepcopy(order_level_bib.orders)
        service = update.OrderLevelBibUpdater(
            rules=test_constants, update_handler=self.update_handler
        )
        updated_bibs = service.update(
            [order_level_bib], template_data=fake_template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]
