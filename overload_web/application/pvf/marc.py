"""Application services for updating MARC records during processing."""

from __future__ import annotations

import logging

from overload_web.application.pvf import parsing_service, update_service
from overload_web.domain.pvf import models

logger = logging.getLogger(__name__)


class MarcServiceHandler:
    def __init__(
        self, parser: parsing_service.BibParser, updater: update_service.BibUpdater
    ) -> None:
        self.parser = parser
        self.updater = updater
        self.validator = parsing_service.BarcodeValidator()

    def apply_updates_by_record_type(
        self, record: models.DomainBib, record_type: str, **kwargs
    ) -> None:
        updates = []
        if record_type == "cat":
            updates.extend(self.updater.get_cat_updates(record=record, **kwargs))
        elif record_type == "sel":
            updates.extend(self.updater.get_sel_updates(record=record, **kwargs))
        else:
            updates.extend(self.updater.get_acq_updates(record=record, **kwargs))
        self.updater.apply_field_updates(record=record, updates=updates)

    def extract_barcodes(self, records: list[models.DomainBib]) -> list[str]:
        return self.validator.validate_unique(barcodes=[i.barcodes for i in records])

    def parse_and_validate_incoming(
        self, data: bytes | list[bytes], vendor: str | None = None
    ) -> list[models.DomainBib]:
        if isinstance(data, list):
            combined_data = self.parser.combine_marc_files(data)
            records = self.parser.parse_marc_data(data=combined_data, vendor=vendor)
        else:
            records = self.parser.parse_marc_data(data=data, vendor=vendor)
        self.validator.validate_unique(barcodes=[i.barcodes for i in records])
        return records

    def validate_output(
        self, barcodes: list[str], processed_recs: list[models.DomainBib]
    ) -> list[str]:
        return self.validator.validate_preserved(
            original_barcodes=barcodes,
            processed_barcodes=[i.barcodes for i in processed_recs],
        )
