import pytest

from overload_web.bib_records.domain_services import serialize


class TestUpdater:
    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize_order(self, acq_bib, caplog):
        service = serialize.OrderLevelBibSerializer()
        marc_binary = service.serialize(records=[acq_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg

    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize_full(self, cat_bib, caplog):
        record_batch = {
            "NEW": [cat_bib],
            "DUP": [cat_bib],
            "DEDUPED": [cat_bib],
        }
        service = serialize.FullLevelBibSerializer()
        marc_binary = service.serialize(record_batches=record_batch)
        assert marc_binary["NEW"].read()[0:2] == b"00"
        assert len(caplog.records) == 3
        assert "Writing MARC binary for record: " in caplog.records[0].msg
