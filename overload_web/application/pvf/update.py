"""Application services for updating MARC records during processing."""

from __future__ import annotations

import logging
from typing import Any

from overload_web.application import ports
from overload_web.domain.pvf import marc_rules, models

logger = logging.getLogger(__name__)


class BibUpdater:
    def __init__(
        self,
        bib_id_tag: str,
        collection: str | None,
        default_loc: str | None,
        library: str,
        order_mapping: dict[str, Any],
        record_type: str,
    ) -> None:
        self.bib_id_tag = bib_id_tag
        self.collection = collection
        self.default_loc = default_loc
        self.library = library
        self.order_mapping = order_mapping
        self.record_type = record_type

    def get_acq_updates(
        self, record: models.DomainBib, template_data: dict[str, Any]
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to update in processed acq bib record"""
        updates: list[Any] = []
        record.apply_order_template(template_data)
        updates.extend(
            marc_rules.FieldRules.update_order_fields(
                record=record, mapping=self.order_mapping
            )
        )
        updates.append(
            marc_rules.FieldRules.add_bib_id(record=record, tag=self.bib_id_tag)
        )
        if record.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record=record))
        return [i for i in updates if i]

    def get_cat_updates(
        self, record: models.DomainBib
    ) -> list[marc_rules.MarcFieldUpdateValues]:
        """Get list of MARC fields to update in processed full-level bib record"""
        updates: list[Any] = []
        updates.extend(marc_rules.FieldRules.add_vendor_fields(record=record))
        updates.append(
            marc_rules.FieldRules.add_bib_id(record=record, tag=self.bib_id_tag)
        )
        if record.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record=record))
            updates.append(
                marc_rules.FieldRules.update_bt_series_call_no(record=record)
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
                record=record, mapping=self.order_mapping
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
            marc_rules.FieldRules.add_bib_id(record=record, tag=self.bib_id_tag)
        )
        if record.library == "nypl":
            updates.append(marc_rules.FieldRules.update_910_field(record=record))
        return [i for i in updates if i]

    def update_record(
        self,
        record: models.DomainBib,
        handler: ports.MarcUpdateHandlerPort,
        updates: list[marc_rules.MarcFieldUpdateValues],
    ) -> None:
        """Update and add MARC fields to bib record"""
        bib = handler.create_bib_from_domain(record=record)
        handler.update_fields(field_updates=updates, bib=bib)
        bib.leader = marc_rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()
