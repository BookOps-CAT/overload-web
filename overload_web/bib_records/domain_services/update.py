"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)

T = TypeVar("T")


class UpdateStep(Protocol):
    def apply(self, ctx: Any) -> None: ...  # pragma: no branch


class MarcContext(Protocol[T]):
    bib_rec: T
    record: bibs.DomainBib
    order_mapping: dict[str, Any]
    default_loc: str | None
    bib_id_tag: str


class MarcContextFactory(Protocol):
    def create(self, record: bibs.DomainBib, **kwargs: Any) -> MarcContext: ...


class MarcUpdateStrategy(Protocol):
    @property
    def pipeline(self) -> list[UpdateStep]: ...  # pragma: no branch
    def create_context(
        self, record: bibs.DomainBib, **kwargs: Any
    ) -> MarcContext: ...  # pragma: no branch


class BibUpdater:
    def __init__(self, strategy: MarcUpdateStrategy) -> None:
        self.strategy = strategy

    def update(
        self, records: list[bibs.DomainBib], **kwargs: Any
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.
                This kwarg is only used for order-level records.

        Returns:
            A list of updated records as `DomainBib` objects
        """
        out = []
        for record in records:
            ctx = self.strategy.create_context(record=record, **kwargs)
            for step in self.strategy.pipeline:
                step.apply(ctx)
            record.binary_data = ctx.bib_rec.as_marc()
            out.append(record)
        return out
