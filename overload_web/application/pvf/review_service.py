"""Application services for reviewing MARC records after processing."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import marc_rules, models

logger = logging.getLogger(__name__)


class BibReviewer:
    def __init__(self, handler: ports.MarcUpdaterPort) -> None:
        self.handler = handler

    def review_batch(self, records: list[models.DomainBib]) -> dict[str, Any]:
        """Merges item fields from duplicate records into the base record."""
        out: dict[str, list[models.DomainBib]] = {"NEW": [], "DUP": [], "DEDUPED": []}
        dup_groups = defaultdict(list)

        for record in records:
            if record.action and record.action == "attach":
                out["DUP"].append(record)
            else:
                out["NEW"].append(record)
                dup_groups[record.control_number].append(record)
        for control_number, group in dup_groups.items():
            # only deduplicate new recs if there are groups with multiple records
            if len(group) > 1 and control_number is not None:
                return {"NEW": out["NEW"], "DUP": out["DUP"], "TO_DEDUPE": dup_groups}
        return {"NEW": out["NEW"], "DUP": out["DUP"]}

    def deduplicate(
        self, records: list[models.DomainBib]
    ) -> dict[str, list[models.DomainBib]]:
        """Review and deduplicate a batch of processed full-level MARC records."""
        batches = self.review_batch(records=records)
        if not batches.get("TO_DEDUPE"):
            return {"NEW": batches["NEW"], "DUP": batches["DUP"], "DEDUPED": []}
        deduped = []
        for control_number, group in batches["TO_DEDUPE"].items():
            if len(group) == 1:
                deduped.append(group[0])
            elif len(group) > 1 and control_number is not None:
                base_rec = group[0]
                other_fields = [i.parsed_fields for i in group[1:]]
                item_tags = marc_rules.FieldRules.get_item_field_criteria(
                    fields=base_rec.parsed_fields, library=base_rec.library
                )
                item_fields = marc_rules.FieldRules.get_item_fields(
                    fields=other_fields, criteria=item_tags
                )
                bib = self.handler.create_bib_from_domain(record=base_rec)
                self.handler.update_fields(field_updates=item_fields, bib=bib)
                base_rec.binary_data = bib.as_marc()
                deduped.append(base_rec)
            else:
                deduped.extend(group)
        return {"NEW": batches["NEW"], "DUP": batches["DUP"], "DEDUPED": deduped}
