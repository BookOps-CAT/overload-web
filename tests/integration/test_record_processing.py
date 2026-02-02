import pytest

from overload_web.application import record_service
from overload_web.bib_records.domain_models import bibs
from overload_web.bib_records.infrastructure import marc_mapper, marc_updater
from overload_web.shared.errors import OverloadError


@pytest.fixture
def service_components(
    fake_fetcher, get_constants, library, collection, record_type
) -> tuple:
    if record_type == "cat":
        return (
            fake_fetcher,
            marc_mapper.FullRecordMarcMapper(
                rules=get_constants["mapper_rules"],
                library=library,
                record_type=record_type,
            ),
            record_service.MatchAnalyzerFactory().make(
                library=library, record_type=record_type, collection=collection
            ),
            marc_updater.BookopsMarcUpdateStrategy(
                rules=get_constants, record_type=record_type, library=library
            ),
        )
    else:
        return (
            fake_fetcher,
            marc_mapper.OrderLevelMarcMapper(
                rules=get_constants["mapper_rules"],
                library=library,
                record_type=record_type,
            ),
            record_service.MatchAnalyzerFactory().make(
                library=library, record_type=record_type, collection=collection
            ),
            marc_updater.BookopsMarcUpdateStrategy(
                rules=get_constants, record_type=record_type, library=library
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
            bib_mapper=service_components[1],
            analyzer=service_components[2],
            update_strategy=service_components[3],
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
            bib_mapper=service_components[1],
            analyzer=service_components[2],
            update_strategy=service_components[3],
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
            bib_mapper=service_components[1],
            analyzer=service_components[2],
            update_strategy=service_components[3],
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
            bib_mapper=service_components[1],
            analyzer=service_components[2],
            update_strategy=service_components[3],
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
