"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)

T = TypeVar("T")


class UpdateStep(Protocol):
    """A step in the bib record update workflow."""

    def apply(self, ctx: Any) -> None: ...  # pragma: no branch


class MarcContext(Protocol[T]):
    """A domain entity used in the bib record update workflow"""

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

    def update(self, record: bibs.DomainBib, **kwargs: Any) -> bibs.DomainBib:
        """
        Update a bibliographic record.

        Args:
            record:
                A parsed bibliographic record
            template_data:
                A dictionary containing template data to be used in updating records.
                This kwarg is only used for order-level records.

        Returns:
            An updated records as a `DomainBib` object
        """
        ctx = self.strategy.create_context(record=record, **kwargs)
        for step in self.strategy.pipeline:
            step.apply(ctx)
        record.binary_data = ctx.bib_rec.as_marc()
        return record
