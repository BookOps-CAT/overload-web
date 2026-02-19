import io

import pytest

from overload_web.application.commands import ProcessFullRecords, ProcessOrderRecords
from overload_web.application.services import record_service
from overload_web.domain.errors import OverloadError
from overload_web.infrastructure import marc_engine


class TestProcessBatch:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file(
        self, library, fake_fetcher, engine_config
    ):
        command_handler = record_service.ProcessingHandler(
            fetcher=fake_fetcher, engine=marc_engine.MarcEngine(rules=engine_config)
        )
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessFullRecords.execute(
            marc_data, handler=command_handler, file_name="foo.mrc"
        )
        assert isinstance(out.duplicate_records, list)
        assert isinstance(out.new_records, list)
        assert isinstance(out.deduplicated_records, list)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file(
        self, library, fake_fetcher, engine_config
    ):
        command_handler = record_service.ProcessingHandler(
            fetcher=fake_fetcher, engine=marc_engine.MarcEngine(rules=engine_config)
        )
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessOrderRecords.execute(
            marc_data,
            handler=command_handler,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            file_name="foo.mrc",
        )
        assert isinstance(out.records, list)
        assert isinstance(out.record_stream, io.BytesIO)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config
    ):
        command_handler = record_service.ProcessingHandler(
            fetcher=fake_fetcher, engine=marc_engine.MarcEngine(rules=engine_config)
        )
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            ProcessFullRecords.execute(
                marc_data, handler=command_handler, file_name="foo.mrc"
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config
    ):
        command_handler = record_service.ProcessingHandler(
            fetcher=fake_fetcher, engine=marc_engine.MarcEngine(rules=engine_config)
        )
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            ProcessOrderRecords.execute(
                marc_data,
                handler=command_handler,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                file_name="foo.mrc",
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)
