import pytest

from overload_web.application.ports import marc_writer


class TestUpdater:
    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize_order(self, order_level_bib, caplog):
        service = marc_writer.BibSerializer()
        marc_binary = service.serialize(records=[order_level_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
