"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from overload_web.domain.pvf import models
from overload_web.domain.shared import fields

logger = logging.getLogger(__name__)


@dataclass
class TargetFieldCriteria:
    tag: str
    indicators: tuple[str, str]
    subfield_code: str
    subfield_starts_with: str | None = None


@dataclass
class MarcFieldUpdateValues:
    """Value object used to define updates to be made to a MARC field."""

    tag: str
    ind1: str
    ind2: str
    subfields: list[dict[str, str]]
    delete_all_by_tag: bool = False
    target_to_delete: TargetFieldCriteria | None = None


class FieldRules:
    """Functions that create `MarcFieldUpdateValues` to be used to update MARC fields"""

    @staticmethod
    def add_bib_id(record: models.DomainBib, tag: str) -> MarcFieldUpdateValues | None:
        """Creates a new bib ID field."""
        if record.bib_id:
            return MarcFieldUpdateValues(
                delete_all_by_tag=True,
                tag=tag,
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": record.bib_id}],
            )
        return None

    @staticmethod
    def add_command_tag(
        format: str | None, default_loc: str | None, fields: list[fields.ParsedField]
    ) -> MarcFieldUpdateValues | None:
        """Creates a new or updated command tag field."""
        if not format and not default_loc:
            return None
        command_tag: str | None = None
        for field in fields:
            if field.tag == "949" and field.indicators == (" ", " "):
                for subfield in field.subfields:
                    if subfield.code == "a" and subfield.value.startswith("*"):
                        command_tag = subfield.value.strip()
                        if "bn=" in command_tag:
                            return None
                        else:
                            break
        if not command_tag:
            if not format:
                command_tag = f"*bn={default_loc};"
            elif format and not default_loc:
                command_tag = f"*b2={format};"
            else:
                command_tag = f"*b2={format};bn={default_loc};"
            return MarcFieldUpdateValues(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": command_tag}],
            )
        if command_tag and not default_loc:
            return None
        return MarcFieldUpdateValues(
            tag="949",
            ind1=" ",
            ind2=" ",
            subfields=[
                {
                    "code": "a",
                    "value": f"{command_tag.removesuffix(';')};bn={default_loc};",
                }
            ],
            target_to_delete=TargetFieldCriteria(
                tag="949",
                indicators=(" ", " "),
                subfield_code="a",
                subfield_starts_with="*",
            ),
        )

    @staticmethod
    def add_item_fields(
        items: list[fields.ParsedField], ind2: str, tag: str
    ) -> list[MarcFieldUpdateValues]:
        """Creates list of new item records to add to a record"""
        new_items = []
        for item in items:
            if item.indicators == (" ", ind2):
                new_items.append(
                    MarcFieldUpdateValues(
                        tag=tag,
                        ind1=" ",
                        ind2=ind2,
                        subfields=[
                            {"code": i.code, "value": i.value} for i in item.subfields
                        ],
                    )
                )
        return new_items

    @staticmethod
    def add_vendor_fields(record: models.DomainBib) -> list[MarcFieldUpdateValues]:
        """Creates a list of fields for a full MARC record based on `VendorInfo`."""
        field_objs = []
        bib_fields = getattr(record.vendor_info, "bib_fields", [])
        for field_data in bib_fields:
            field_objs.append(
                MarcFieldUpdateValues(
                    tag=field_data["tag"],
                    ind1=field_data["ind1"],
                    ind2=field_data["ind2"],
                    subfields=[
                        {"code": field_data["code"], "value": field_data["value"]}
                    ],
                )
            )
        return field_objs

    @staticmethod
    def update_leader(leader: str) -> str:
        """Updates record leader for UTF-8"""
        return leader[:9] + "a" + leader[10:]

    @staticmethod
    def update_910_field(record: models.DomainBib) -> MarcFieldUpdateValues:
        """Adds 910 field for branches or research if applicable."""
        return MarcFieldUpdateValues(
            delete_all_by_tag=True,
            tag="910",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": record.collection}],
        )

    @staticmethod
    def update_bt_series_call_no(
        record: models.DomainBib,
    ) -> MarcFieldUpdateValues | None:
        """Updates call number for B&T Series materials."""
        call_no = record.branch_call_number
        if (
            not record.vendor == "BT SERIES"
            or not call_no
            or not record.collection == "BL"
        ):
            return None
        new_subfields = []
        pos = 0

        if call_no[:6] == "J SPA ":
            new_subfields.append({"code": "p", "value": "J SPA"})
        elif call_no[:2] == "J ":
            new_subfields.append({"code": "p", "value": "J"})

        if "GRAPHIC " in call_no:
            new_subfields.append({"code": "f", "value": "GRAPHIC"})
        elif "HOLIDAY " in call_no:
            new_subfields.append({"code": "f", "value": "HOLIDAY"})
        elif "YR " in call_no:
            new_subfields.append({"code": "f", "value": "YR"})

        if "GN FIC " in call_no:
            pos = call_no.index("GN FIC ") + 7
            new_subfields.append({"code": "a", "value": "GN FIC"})
        elif "FIC " in call_no:
            pos = call_no.index("FIC ") + 4
            new_subfields.append({"code": "a", "value": "FIC"})
        elif "PIC " in call_no:
            pos = call_no.index("PIC ") + 4
            new_subfields.append({"code": "a", "value": "PIC"})
        elif call_no[:4] == "J E ":
            pos = call_no.index("J E ") + 4
            new_subfields.append({"code": "a", "value": "E"})
        elif call_no[:8] == "J SPA E ":
            pos = call_no.index("J SPA E ") + 8
            new_subfields.append({"code": "a", "value": "E"})

        new_subfields.append({"code": "c", "value": call_no[pos:]})
        new_call_no = " ".join([i["value"] for i in new_subfields])
        if call_no != new_call_no:
            raise ValueError(
                "Constructed call number does not match original. "
                f"New={new_call_no}, Original={call_no}"
            )
        return MarcFieldUpdateValues(
            delete_all_by_tag=True,
            tag="091",
            ind1=" ",
            ind2=" ",
            subfields=new_subfields,
        )

    @staticmethod
    def update_order_fields(
        record: models.DomainBib, mapping: dict[str, Any]
    ) -> list[MarcFieldUpdateValues]:
        """Updates order record fields based on template data applied to DomainBib"""
        fields = []
        for order in record.orders:
            order_data = order.map_to_marc(rules=mapping)
            for tag, subfield_values in order_data.items():
                subfields = []
                for k, v in subfield_values.items():
                    if v is None:
                        continue
                    if isinstance(v, list):
                        subfields.extend([{"code": k, "value": str(i)} for i in v])
                    else:
                        subfields.append({"code": k, "value": str(v)})
                fields.append(
                    MarcFieldUpdateValues(
                        tag=tag, ind1=" ", ind2=" ", subfields=subfields
                    )
                )
        return fields
