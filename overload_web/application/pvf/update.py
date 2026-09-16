"""Application services for updating MARC records during processing."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import marc_rules, models

logger = logging.getLogger(__name__)


class BatchReviewer:
    @staticmethod
    def review_batch(records: list[models.DomainBib]) -> dict[str, Any]:
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


class BibFieldUpdater:
    def __init__(
        self,
        bib_id_tag: str,
        collection: str | None,
        default_loc: str | None,
        library: str,
        order_mapping: dict[str, Any],
    ) -> None:
        self.bib_id_tag = bib_id_tag
        self.collection = collection
        self.default_loc = default_loc
        self.library = library
        self.order_mapping = order_mapping

    def get_acq_updates(
        self, record: models.DomainBib, template_data: dict[str, Any]
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to update in processed acq bib record"""
        updates: list[Any] = []
        record.apply_order_template(template_data)
        updates.extend(
            marc_rules.FieldRules.update_order_fields(
                orders=record.orders, mapping=self.order_mapping
            )
        )
        updates.append(
            marc_rules.FieldRules.add_bib_id(bib_id=record.bib_id, tag=self.bib_id_tag)
        )
        if self.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record.collection))
        return [i for i in updates if i]

    def get_cat_updates(
        self, record: models.DomainBib
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to update in processed full-level bib record"""
        updates: list[Any] = []

        updates.extend(
            marc_rules.FieldRules.add_vendor_fields(
                getattr(record.vendor_info, "bib_fields", [])
            )
        )
        updates.append(
            marc_rules.FieldRules.add_bib_id(bib_id=record.bib_id, tag=self.bib_id_tag)
        )
        if self.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record.collection))
            updates.append(
                marc_rules.FieldRules.update_bt_series_call_no(
                    call_no=record.branch_call_number,
                    vendor=record.vendor,
                    collection=record.collection,
                )
            )
        return [i for i in updates if i]

    def get_sel_updates(
        self, record: models.DomainBib, template_data: dict[str, Any]
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Update and add MARC fields to sel bib record"""
        updates: list[Any] = []
        record.apply_order_template(template_data)
        updates.extend(
            marc_rules.FieldRules.update_order_fields(
                orders=record.orders, mapping=self.order_mapping
            )
        )
        updates.append(
            marc_rules.FieldRules.add_command_tag(
                fields=record.parsed_fields,
                format=template_data.get("format"),
                default_loc=self.default_loc,
            )
        )
        updates.append(
            marc_rules.FieldRules.add_bib_id(bib_id=record.bib_id, tag=self.bib_id_tag)
        )
        if self.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record.collection))
        return [i for i in updates if i]


class BibRecordUpdater:
    @staticmethod
    def update_record(
        record: models.DomainBib,
        handler: ports.MarcUpdaterPort,
        updates: list[marc_rules.MarcFieldUpdateValues],
    ) -> None:
        """Update and add MARC fields to bib record"""
        bib = handler.create_bib_from_domain(record=record)
        handler.update_fields(field_updates=updates, bib=bib)
        handler.update_leader_encoding(leader=bib.leader, bib=bib)
        record.binary_data = bib.as_marc()

    @staticmethod
    def deduplicate(
        records: list[models.DomainBib], handler: ports.MarcUpdaterPort
    ) -> dict[str, list[models.DomainBib]]:
        """Review and deduplicate a batch of processed full-level MARC records."""
        batches = BatchReviewer.review_batch(records=records)
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
                bib = handler.create_bib_from_domain(record=base_rec)
                handler.update_fields(field_updates=item_fields, bib=bib)
                base_rec.binary_data = bib.as_marc()
                deduped.append(base_rec)
            else:
                deduped.extend(group)
        return {"NEW": batches["NEW"], "DUP": batches["DUP"], "DEDUPED": deduped}
