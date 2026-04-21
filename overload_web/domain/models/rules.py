"""Domain models defining rules used to update MARC records during processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class AcquisitionUpdates:
    """Returns a list of fields to be updated in an acq record during processing"""

    @staticmethod
    def field_list(record: bibs.DomainBib, context: Any) -> list[MarcFieldUpdateValues]:
        updates: list[Any] = []
        updates.extend(
            FieldRules.update_order_fields(
                record=record, mapping=context.marc_order_mapping
            )
        )
        updates.append(FieldRules.add_bib_id(record=record, tag=context.bib_id_tag))
        if context.library == "nypl":
            updates.append(FieldRules.update_910_field(record=record))
        return [i for i in updates if i]


class CatalogingUpdates:
    """Returns a list of fields to be updated in a cat record during processing"""

    @staticmethod
    def field_list(record: bibs.DomainBib, context: Any) -> list[MarcFieldUpdateValues]:
        updates: list[Any] = []
        updates.extend(FieldRules.add_vendor_fields(record=record))
        updates.append(FieldRules.add_bib_id(record=record, tag=context.bib_id_tag))
        if context.library == "nypl":
            updates.append(FieldRules.update_910_field(record=record))
            updates.append(FieldRules.update_bt_series_call_no(record=record))
        return [i for i in updates if i]


class SelectionUpdates:
    """Returns a list of fields to be updated in a sel record during processing"""

    @staticmethod
    def field_list(
        record: bibs.DomainBib,
        context: Any,
        format: str | None = None,
        command_tag: Any | None = None,
    ) -> list[MarcFieldUpdateValues]:
        updates: list[Any] = []
        updates.extend(
            FieldRules.update_order_fields(
                record=record, mapping=context.marc_order_mapping
            )
        )
        updates.append(
            FieldRules.add_command_tag(
                field=command_tag, format=format, default_loc=context.default_loc
            )
        )
        updates.append(FieldRules.add_bib_id(record=record, tag=context.bib_id_tag))
        if context.library == "nypl":
            updates.append(FieldRules.update_910_field(record=record))
        return [i for i in updates if i]


@dataclass
class MarcFieldUpdateValues:
    """Value object used to define updates to be made to a MARC field."""

    tag: str
    ind1: str
    ind2: str
    subfields: list[dict[str, str]]
    delete: bool = False
    original: Any | None = None


class FieldRules:
    """Functions that create `MarcFieldUpdateValues` to be used to update MARC fields"""

    @staticmethod
    def add_bib_id(record: bibs.DomainBib, tag: str) -> MarcFieldUpdateValues | None:
        """Creates a new bib ID field."""
        if record.bib_id:
            return MarcFieldUpdateValues(
                delete=True,
                tag=tag,
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": record.bib_id}],
            )
        return None

    @staticmethod
    def add_command_tag(
        format: str | None, default_loc: str | None, field: Any | None
    ) -> MarcFieldUpdateValues | None:
        """Creates a new or updated command tag field."""
        if not format and not default_loc:
            return None
        if not field:
            if format:
                command_tag = f"*b2={format};"
                if default_loc:
                    command_tag = f"*b2={format};bn={default_loc};"
                else:
                    command_tag = f"*b2={format};"
                return MarcFieldUpdateValues(
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": command_tag}],
                )
            return MarcFieldUpdateValues(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": f"*bn={default_loc};"}],
            )
        if not default_loc:
            return None
        command_tag = field["a"].strip()
        if "bn=" in command_tag:
            return None
        elif "bn=" not in command_tag[-1] == ";":
            return MarcFieldUpdateValues(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": f"{command_tag}bn={default_loc};"}],
                original=field,
            )
        else:
            return MarcFieldUpdateValues(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": f"{command_tag};bn={default_loc};"}],
                original=field,
            )

    @staticmethod
    def add_vendor_fields(record: bibs.DomainBib) -> list[MarcFieldUpdateValues]:
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
    def update_910_field(record: bibs.DomainBib) -> MarcFieldUpdateValues:
        """Adds 910 field for branches or research if applicable."""
        return MarcFieldUpdateValues(
            delete=True,
            tag="910",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": record.collection}],
        )

    @staticmethod
    def update_bt_series_call_no(
        record: bibs.DomainBib,
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
            delete=True, tag="091", ind1=" ", ind2=" ", subfields=new_subfields
        )

    @staticmethod
    def update_order_fields(
        record: bibs.DomainBib, mapping: dict[str, Any]
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
