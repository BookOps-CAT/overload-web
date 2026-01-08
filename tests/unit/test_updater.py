import copy

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain_services import update
from overload_web.bib_records.infrastructure import marc_updater


class TestUpdater:
    update_handler = marc_updater.BookopsMarcUpdateHandler()

    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_update_cat_bpl(self, cat_bib):
        original_bib = Bib(copy.deepcopy(cat_bib.binary_data), library=cat_bib.library)

        cat_bib.bib_id = "12345"
        service = update.FullLevelBibUpdater(
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([cat_bib])
        updated_bib = Bib(updated_bibs[0].binary_data, library=updated_bibs[0].library)
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("907")) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_update_cat_nypl(self, cat_bib):
        original_bib = Bib(copy.deepcopy(cat_bib.binary_data), library=cat_bib.library)
        cat_bib.bib_id = "12345"
        service = update.FullLevelBibUpdater(
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([cat_bib])
        updated_bib = Bib(updated_bibs[0].binary_data, library=updated_bibs[0].library)
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("945")) == 1

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_cat_vendor_updates(self, make_domain_bib, library):
        dto = make_domain_bib(
            {
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
            "cat",
        )
        original_bib = copy.deepcopy(Bib(dto.binary_data, library=library))
        service = update.FullLevelBibUpdater(
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([dto])
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_acq(self, acq_bib, fake_template_data, test_constants):
        original_orders = copy.deepcopy(acq_bib.orders)
        assert acq_bib.record_type == "acq"
        service = update.OrderLevelBibUpdater(
            rules=test_constants,
            update_handler=self.update_handler,
        )
        updated_bibs = service.update([acq_bib], template_data=fake_template_data)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_sel(self, sel_bib, fake_template_data, test_constants):
        original_orders = copy.deepcopy(sel_bib.orders)
        assert sel_bib.record_type == "sel"
        service = update.OrderLevelBibUpdater(
            rules=test_constants, update_handler=self.update_handler
        )
        updated_bibs = service.update([sel_bib], template_data=fake_template_data)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]
