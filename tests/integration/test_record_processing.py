import io

import pytest

from overload_web.application.commands import ProcessBatch
from overload_web.application.services import record_service
from overload_web.domain.errors import OverloadError
from overload_web.domain.models import bibs
from overload_web.infrastructure.marc import engine


@pytest.fixture
def service_components(
    fake_fetcher, engine_config, library, collection, record_type
) -> tuple:
    return (
        fake_fetcher,
        engine.MarcEngine(rules=engine_config),
        record_service.MatchAnalyzerFactory().make(
            library=library, record_type=record_type, collection=collection
        ),
    )


class TestRecordProcessingService:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file(self, library, service_components):
        service = record_service.FullRecordProcessingService(
            bib_fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = service.process_vendor_file(marc_data)
        assert isinstance(out, dict)
        assert isinstance(out["report"], list)
        assert isinstance(out["records"], list)
        assert isinstance(out["records"][0], bibs.DomainBib)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file(self, library, service_components):
        service = record_service.OrderRecordProcessingService(
            bib_fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = service.process_vendor_file(
            data=marc_data,
            template_data={"format": "a"},
            matchpoints={"primary_matchpoint": "isbn"},
            vendor="UNKNOWN",
        )
        assert isinstance(out, dict)
        assert isinstance(out["report"], list)
        assert isinstance(out["records"], list)
        assert isinstance(out["records"][0], bibs.DomainBib)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file_dupes(self, library, service_components):
        service = record_service.FullRecordProcessingService(
            bib_fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            service.process_vendor_file(marc_data)
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file_dupes(self, library, service_components):
        service = record_service.OrderRecordProcessingService(
            bib_fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            service.process_vendor_file(
                data=marc_data,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn"},
                vendor="UNKNOWN",
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)


class TestProcessBatch:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file(self, library, service_components):
        command_handler = record_service.ProcessingHandler(
            fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        records, stats = ProcessBatch.execute_full_records_workflow(
            marc_data, handler=command_handler
        )
        assert isinstance(stats, dict)
        assert isinstance(records, dict)
        assert list(records.keys()) == ["DUP", "NEW", "DEDUPED"]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file(self, library, service_components):
        command_handler = record_service.ProcessingHandler(
            fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        records, stats = ProcessBatch.execute_order_records_workflow(
            marc_data,
            handler=command_handler,
            template_data={"format": "a"},
            matchpoints={"primary_matchpoint": "isbn"},
            vendor="UNKNOWN",
        )
        assert isinstance(stats, dict)
        assert isinstance(records, io.BytesIO)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file_dupes(self, library, service_components):
        command_handler = record_service.ProcessingHandler(
            fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            ProcessBatch.execute_full_records_workflow(
                marc_data, handler=command_handler
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file_dupes(self, library, service_components):
        command_handler = record_service.ProcessingHandler(
            fetcher=service_components[0],
            engine=service_components[1],
            analyzer=service_components[2],
        )
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            ProcessBatch.execute_order_records_workflow(
                marc_data,
                handler=command_handler,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn"},
                vendor="UNKNOWN",
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)
