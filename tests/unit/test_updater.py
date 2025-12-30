import copy

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain import bib_services
from overload_web.bib_records.infrastructure import marc_updater
from overload_web.errors import OverloadError


class TestUpdater:
    @pytest.mark.parametrize("library, collection", [("bpl", "NONE")])
    def test_update_cat_bpl(self, stub_full_bib, stub_constants):
        original_bib = Bib(
            copy.deepcopy(stub_full_bib.binary_data), library=str(stub_full_bib.library)
        )
        stub_full_bib.bib_id = "12345"
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type="cat"
            )
        )
        updated_bibs = stub_service.update([stub_full_bib])
        updated_bib = Bib(
            updated_bibs[0].binary_data, library=str(updated_bibs[0].library)
        )
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("907")) == 1

    @pytest.mark.parametrize("library, collection", [("nypl", "BL"), ("nypl", "RL")])
    def test_update_cat_nypl(self, stub_full_bib, stub_constants):
        original_bib = Bib(
            copy.deepcopy(stub_full_bib.binary_data), library=str(stub_full_bib.library)
        )
        stub_full_bib.bib_id = "12345"
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type="cat"
            )
        )
        updated_bibs = stub_service.update([stub_full_bib])
        updated_bib = Bib(
            updated_bibs[0].binary_data, library=str(updated_bibs[0].library)
        )
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("945")) == 1

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_cat_no_vendor_index(self, stub_order_bib, stub_constants):
        setattr(stub_order_bib, "record_type", bib_services.bibs.RecordType("cat"))
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type="cat"
            )
        )
        with pytest.raises(OverloadError) as exc:
            stub_service.update([stub_order_bib])
        assert str(exc.value) == "Vendor index required for cataloging workflow."

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
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type="cat"
            )
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
    def test_update_acq(self, stub_order_bib, template_data, stub_constants):
        original_orders = copy.deepcopy(stub_order_bib.orders)
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type="acq"
            )
        )
        updated_bibs = stub_service.update(
            [stub_order_bib], template_data=template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    def test_update_sel(self, stub_order_bib, template_data, stub_constants):
        original_orders = copy.deepcopy(stub_order_bib.orders)
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type="sel"
            )
        )
        updated_bibs = stub_service.update(
            [stub_order_bib], template_data=template_data
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    @pytest.mark.parametrize("record_type", ["acq", "sel"])
    def test_update_acq_sel_no_template(
        self, stub_order_bib, stub_constants, record_type
    ):
        setattr(
            stub_order_bib, "record_type", bib_services.bibs.RecordType(record_type)
        )
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type=record_type
            )
        )

        with pytest.raises(OverloadError) as exc:
            stub_service.update([stub_order_bib])
        assert (
            str(exc.value)
            == "Order template required for acquisition or selection workflow."
        )

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_serialize(self, stub_order_bib, caplog, stub_constants, record_type):
        stub_service = bib_services.BibSerializer(
            updater=marc_updater.BookopsMarcUpdater(
                rules=stub_constants, record_type=record_type
            )
        )
        marc_binary = stub_service.serialize(records=[stub_order_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
