import pytest

from overload_web.bib_records.domain_services import serialize


class TestUpdater:
    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize_order(self, stub_acq_bib, caplog):
        stub_service = serialize.OrderLevelBibSerializer()
        marc_binary = stub_service.serialize(records=[stub_acq_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize_full(self, stub_cat_bib, caplog):
        record_batch = {
            "NEW": [stub_cat_bib],
            "DUP": [stub_cat_bib],
            "DEDUPED": [stub_cat_bib],
        }
        stub_service = serialize.FullLevelBibSerializer()
        marc_binary = stub_service.serialize(record_batches=record_batch)
        assert marc_binary["NEW"].read()[0:2] == b"00"
        assert len(caplog.records) == 3
        assert "Writing MARC binary for record: " in caplog.records[0].msg
