import copy

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain import bib_services
from overload_web.bib_records.infrastructure import marc_updater


class TestUpdater:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_update_cat_bpl(self, stub_cat_bib, stub_constants):
        original_bib = Bib(
            copy.deepcopy(stub_cat_bib.binary_data), library=str(stub_cat_bib.library)
        )
        stub_cat_bib.bib_id = "12345"
        stub_service = bib_services.FullLevelBibSerializer(
            updater=marc_updater.BookopsMarcUpdater(rules=stub_constants)
        )
        updated_bibs = stub_service.update([stub_cat_bib])
        updated_bib = Bib(
            updated_bibs[0].binary_data, library=str(updated_bibs[0].library)
        )
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("907")) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_update_cat_nypl(self, stub_cat_bib, stub_constants):
        original_bib = Bib(
            copy.deepcopy(stub_cat_bib.binary_data), library=str(stub_cat_bib.library)
        )
        stub_cat_bib.bib_id = "12345"
        stub_service = bib_services.FullLevelBibSerializer(
            updater=marc_updater.BookopsMarcUpdater(rules=stub_constants)
        )
        updated_bibs = stub_service.update([stub_cat_bib])
        updated_bib = Bib(
            updated_bibs[0].binary_data, library=str(updated_bibs[0].library)
        )
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("945")) == 1

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_cat_vendor_updates(self, make_domain_bib, library, stub_constants):
        dto = make_domain_bib(
            {
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
            "cat",
        )
        original_bib = copy.deepcopy(Bib(dto.binary_data, library=library))
        stub_service = bib_services.FullLevelBibSerializer(
            updater=marc_updater.BookopsMarcUpdater(rules=stub_constants)
        )
        updated_bibs = stub_service.update([dto])
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_acq(self, stub_acq_bib, template_data, stub_constants):
        original_orders = copy.deepcopy(stub_acq_bib.orders)
        assert str(stub_acq_bib.record_type) == "acq"
        stub_service = bib_services.OrderLevelBibSerializer(
            updater=marc_updater.BookopsMarcUpdater(rules=stub_constants)
        )
        updated_bibs = stub_service.update([stub_acq_bib], template_data=template_data)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_sel(self, stub_sel_bib, template_data, stub_constants):
        original_orders = copy.deepcopy(stub_sel_bib.orders)
        assert str(stub_sel_bib.record_type) == "sel"
        stub_service = bib_services.OrderLevelBibSerializer(
            updater=marc_updater.BookopsMarcUpdater(rules=stub_constants)
        )
        updated_bibs = stub_service.update([stub_sel_bib], template_data=template_data)
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize(self, stub_acq_bib, caplog, stub_constants):
        stub_service = bib_services.FullLevelBibSerializer(
            updater=marc_updater.BookopsMarcUpdater(rules=stub_constants)
        )
        marc_binary = stub_service.serialize(records=[stub_acq_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
