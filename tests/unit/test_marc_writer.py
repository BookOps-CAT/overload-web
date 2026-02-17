import pytest

from overload_web.application.services import marc_services


class TestUpdater:
    @pytest.mark.parametrize(
        "library, collection",
        [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
    )
    def test_serialize_order(self, acq_bib, caplog):
        service = marc_services.BibSerializer()
        marc_binary = service.write(records=[acq_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg
