import io
import json
from typing import Any

import pytest

from overload_web.application import record_service
from overload_web.bib_records.domain_services import update
from overload_web.bib_records.infrastructure import marc_mapper, marc_updater


@pytest.fixture(scope="module")
def get_constants() -> dict[str, Any]:
    """Retrieve processing constants from JSON file."""
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


@pytest.fixture
def service_components(
    fake_fetcher, get_constants, library, collection, record_type
) -> tuple:
    mapper = marc_mapper.BookopsMarcMapper(
        rules=get_constants["mapper_rules"], library=library, record_type=record_type
    )
    strategy = marc_updater.BookopsMarcUpdateStrategy(
        rules=get_constants, record_type=record_type, library=library
    )
    return (
        fake_fetcher,
        mapper,
        record_service.MatchAnalyzerFactory().make(
            library=library, record_type=record_type, collection=collection
        ),
        update.BibUpdater(strategy=strategy),
    )


class TestRecordProcessingService:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file(self, service_components):
        service = record_service.FullRecordProcessingService(
            bib_fetcher=service_components[0],
            bib_mapper=service_components[1],
            analyzer=service_components[2],
            updater=service_components[3],
        )
        with open("tests/data/sample.mrc", "rb") as fh:
            marc_data = fh.read()
        processed_files = service.process_vendor_file(marc_data)
        assert isinstance(processed_files, dict)
        assert isinstance(processed_files["DEDUPED"], io.BytesIO)
        assert isinstance(processed_files["DUP"], io.BytesIO)
        assert isinstance(processed_files["NEW"], io.BytesIO)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "rL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file(self, service_components):
        service = record_service.OrderRecordProcessingService(
            bib_fetcher=service_components[0],
            bib_mapper=service_components[1],
            analyzer=service_components[2],
            updater=service_components[3],
        )
        with open("tests/data/sample.mrc", "rb") as fh:
            marc_data = fh.read()
        processed_files = service.process_vendor_file(
            data=marc_data,
            template_data={"format": "a"},
            matchpoints={"primary_matchpoint": "isbn"},
            vendor="UNKNOWN",
        )
        assert isinstance(processed_files, io.BytesIO)
