"""Record updaters for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any, Callable

from overload_web.domain.models import bibs
from overload_web.infrastructure.marc import update_steps

logger = logging.getLogger(__name__)


StepFactory = Callable[[], update_steps.UpdateStep]

WORKFLOW_PIPELINES: dict[str, list[StepFactory]] = {
    "acq": [update_steps.MapOrderTemplateToMarc],
    "cat": [update_steps.AddVendorFields],
    "sel": [
        update_steps.MapOrderTemplateToMarc,
        update_steps.AddCommandTag,
        update_steps.SetDefaultLocation,
    ],
}
LIBRARY_PIPELINES: dict[str, list[StepFactory]] = {
    "nypl": [
        update_steps.AddBibId,
        update_steps.UpdateLeader,
        update_steps.Update910Field,
        update_steps.UpdateBtSeriesCallNo,
    ],
    "bpl": [update_steps.AddBibId, update_steps.UpdateLeader],
}


class BookopsMarcUpdateStrategy:
    def __init__(self, library: str, rules: dict[str, Any], record_type: str) -> None:
        self.rules = rules
        self.record_type = record_type
        self.library = library

    @property
    def pipeline(self) -> list[update_steps.UpdateStep]:
        steps = WORKFLOW_PIPELINES[self.record_type] + LIBRARY_PIPELINES[self.library]
        return [step() for step in steps]

    def create_context(
        self,
        record: bibs.DomainBib,
        **kwargs: Any,
    ) -> update_steps.MarcContext:
        if self.record_type in ["acq", "sel"]:
            return update_steps.OrderMarcContext(
                record=record, rules=self.rules, template_data=kwargs["template_data"]
            )
        return update_steps.MarcContext(record=record, rules=self.rules)
