"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)


class UpdateStep(Protocol):
    def apply(self, ctx: Any) -> None: ...  # pragma: no branch


@runtime_checkable
class MarcUpdateHandler(Protocol):
    pipeline: list[UpdateStep]

    def create_order_marc_ctx(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> Any: ...  # pragma: no branch

    def create_full_marc_ctx(
        self, record: bibs.DomainBib
    ) -> Any: ...  # pragma: no branch


class BaseBibUpdater:
    def __init__(self, handler: MarcUpdateHandler) -> None:
        self.handler = handler


class OrderLevelBibUpdater(BaseBibUpdater):
    def update(
        self, records: list[bibs.DomainBib], template_data: dict[str, Any]
    ) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `DomainBib` objects
        """
        out = []
        for record in records:
            ctx = self.handler.create_order_marc_ctx(
                record=record, template_data=template_data
            )
            for step in self.handler.pipeline:
                step.apply(ctx)

            record.binary_data = ctx.bib_rec.as_marc()
            out.append(record)
        return out


class FullLevelBibUpdater(BaseBibUpdater):
    def update(self, records: list[bibs.DomainBib]) -> list[bibs.DomainBib]:
        """
        Update full-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `DomainBib` objects.

        Returns:
            A list of updated records as `DomainBib` objects
        """
        out = []
        for record in records:
            ctx = self.handler.create_full_marc_ctx(record=record)
            for step in self.handler.pipeline:
                step.apply(ctx)
            record.binary_data = ctx.bib_rec.as_marc()
            out.append(record)
        return out
