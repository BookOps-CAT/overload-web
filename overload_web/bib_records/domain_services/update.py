"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar

from overload_web.bib_records.domain_models import bibs, matches

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
        self, records: list[matches.MatchDecisionResult], **kwargs: Any
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records and associated data as
                `MatchDecisionResult` objects.
            template_data:
                A dictionary containing template data to be used in updating records.
                This kwarg is only used for order-level records.

        Returns:
            A list of updated records as `DomainBib` objects
        """
        out = []
        for record in records:
            record.bib.update_bib_id(record.decision.target_bib_id)
            ctx = self.strategy.create_context(record=record.bib, **kwargs)
            for step in self.strategy.pipeline:
                step.apply(ctx)
            record.bib.binary_data = ctx.bib_rec.as_marc()
            out.append(record.bib)
        return out
