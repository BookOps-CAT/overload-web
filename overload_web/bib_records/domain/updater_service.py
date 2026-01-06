"""Domain service for pupdating bib records"""

from __future__ import annotations

import io
import logging
from typing import Any, BinaryIO

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class OrderLevelBibUpdater:
    def __init__(
        self,
        rules: dict[str, dict[str, str]],
        context_handler: marc_protocols.MarcContextHandler,
    ) -> None:
        self.rules = rules
        self.context_handler = context_handler

    def _update_order_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        ctx = self.context_handler.create_order_marc_ctx(
            record=record, template_data=template_data, rules=self.rules
        )
        pipeline = self.context_handler.order_pipelines[str(record.record_type)]
        for step in pipeline:
            step.apply(ctx)
        library_ctx = self.context_handler.create_library_ctx(
            bib_rec=ctx.bib_rec,
            bib_id=record.bib_id,
            vendor=template_data.get("vendor"),
        )
        policies = self.context_handler.library_pipelines[str(record.library)]
        for policy in policies:
            policy.apply(library_ctx)

        record.binary_data = ctx.bib_rec.as_marc()
        return record

    def update(
        self, records: list[bibs.DomainBib], template_data: dict[str, Any]
    ) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            rec = self._update_order_record(record=record, template_data=template_data)
            out.append(rec)
        return out

    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Update bibliographic records and serialize into a binary MARC stream.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.__dict__}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data


class FullLevelBibUpdater:
    def __init__(self, context_handler: marc_protocols.MarcContextHandler) -> None:
        self.context_handler = context_handler

    def _update_full_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        ctx = self.context_handler.create_full_marc_ctx(record=record)
        pipeline = self.context_handler.full_record_pipelines[str(record.record_type)]
        for step in pipeline:
            step.apply(ctx)
        library_ctx = self.context_handler.create_library_ctx(
            bib_rec=ctx.bib_rec, bib_id=record.bib_id, vendor=record.vendor
        )
        policies = self.context_handler.library_pipelines[str(record.library)]
        for policy in policies:
            policy.apply(library_ctx)
        record.binary_data = ctx.bib_rec.as_marc()
        return record

    def update(self, records: list[bibs.DomainBib]) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            rec = self._update_full_record(record=record)
            out.append(rec)
        return out

    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Update bibliographic records and serialize into a binary MARC stream.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.__dict__}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data
