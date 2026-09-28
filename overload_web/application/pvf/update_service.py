"""Application services for updating MARC records during processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import marc_rules, models

logger = logging.getLogger(__name__)


@dataclass
class UpdateRules:
    bib_id_tag: str
    collection: str | None
    default_loc: str | None
    library: str
    order_mapping: dict[str, Any]


class BibUpdater:
    def __init__(self, handler: ports.MarcUpdaterPort, rules: UpdateRules) -> None:
        self.bib_id_tag = rules.bib_id_tag
        self.default_loc = rules.default_loc
        self.handler = handler
        self.library = rules.library
        self.order_mapping = rules.order_mapping

    def apply_field_updates(
        self, record: models.DomainBib, updates: list[marc_rules.MarcFieldUpdateValues]
    ) -> None:
        """Update and add MARC fields to bib record"""
        bib = self.handler.create_bib_from_domain(record=record)
        self.handler.update_fields(field_updates=updates, bib=bib)
        self.handler.update_leader_encoding(leader=bib.leader, bib=bib)
        record.binary_data = bib.as_marc()

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
