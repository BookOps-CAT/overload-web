from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar, runtime_checkable

from overload_web.domain.models import bibs
from overload_web.domain.rules import vendor_rules

logger = logging.getLogger(__name__)

T = TypeVar("T")  # variable bookops_marc `Bib` type


@runtime_checkable
class MarcUpdaterPort(Protocol[T]):
    """Port defining what the application expects from a MARC updater."""

    config: Any

    def _get_call_no_field(self, bib: T) -> str | None: ...

    def _get_command_tag_field(self, bib: T) -> Any | None: ...

    def create_bib(self, record: bibs.DomainBib) -> T: ...

    def apply_updates(self, record: bibs.DomainBib, updates: list[Any], bib: T) -> None:
        """Update a MARC record according to rules and record type."""
        ...


class BibUpdater:
    def __init__(self, engine: MarcUpdaterPort) -> None:
        self.engine = engine

    def update_record(self, record: bibs.DomainBib, **kwargs: Any) -> None:

        template_data = kwargs.get("template_data", {})
        bib = self.engine.create_bib(record=record)

        updates = vendor_rules.VendorRules.fields_to_update(
            record=record,
            template_data=template_data,
            call_no=self.engine._get_call_no_field(bib),
            command_tag=self.engine._get_command_tag_field(bib),
            context=self.engine.config,
        )
        self.engine.apply_updates(record=record, bib=bib, updates=updates)
