from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class VendorRules:
    @staticmethod
    def fields_to_update(
        record: bibs.DomainBib,
        context: Any,
        format: str | None = None,
        command_tag: Any | None = None,
        call_no: str | None = None,
    ) -> list[Any]:
        updates: list[Any] = []

        if context.record_type == "cat":
            bib_fields = getattr(record.vendor_info, "bib_fields", [])
            updates.extend(FieldRules.add_vendor_fields(bib_fields=bib_fields))
        else:
            updates.extend(
                FieldRules.update_order_fields(
                    record=record, mapping=context.marc_order_mapping
                )
            )
            if context.record_type == "sel":
                updates.append(
                    FieldRules.add_command_tag(
                        field=command_tag,
                        format=format,
                        default_loc=context.default_loc,
                    )
                )
        updates.append(
            FieldRules.add_bib_id(bib_id=record.bib_id, tag=context.bib_id_tag)
        )
        if context.library == "nypl":
            updates.append(FieldRules.update_910_field(collection=record.collection))
            if record.collection == "BL" and context.record_type == "cat":
                updates.append(
                    FieldRules.update_bt_series_call_no(
                        call_no=call_no, vendor=record.vendor
                    )
                )
        return [i for i in updates if i]


@dataclass
class MarcFieldUpdate:
    tag: str
    ind1: str
    ind2: str
    subfields: list[dict[str, str]]
    delete: bool = False
    original: Any | None = None


class FieldRules:
    @staticmethod
    def add_bib_id(bib_id: str | None, tag: str) -> MarcFieldUpdate | None:
        if bib_id:
            return MarcFieldUpdate(
                delete=True,
                tag=tag,
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": bib_id}],
            )
        return None

    @staticmethod
    def add_command_tag(
        format: str | None, default_loc: str | None, field: Any | None
    ) -> MarcFieldUpdate | None:
        if not format and not default_loc:
            return None
        if not field:
            if format:
                command_tag = f"*b2={format};"
                if default_loc:
                    command_tag = f"*b2={format};bn={default_loc};"
                else:
                    command_tag = f"*b2={format};"
                return MarcFieldUpdate(
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": command_tag}],
                )
            return MarcFieldUpdate(
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
            return MarcFieldUpdate(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": f"{command_tag}bn={default_loc};"}],
                original=field,
            )
        else:
            return MarcFieldUpdate(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": f"{command_tag};bn={default_loc};"}],
                original=field,
            )

    @staticmethod
    def add_vendor_fields(bib_fields: list[dict[str, Any]]) -> list[MarcFieldUpdate]:
        field_objs = []
        for field_data in bib_fields:
            field_objs.append(
                MarcFieldUpdate(
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
        return leader[:9] + "a" + leader[10:]

    @staticmethod
    def update_910_field(collection: str) -> MarcFieldUpdate:
        return MarcFieldUpdate(
            delete=True,
            tag="910",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": collection}],
        )

    @staticmethod
    def update_bt_series_call_no(
        vendor: str | None, call_no: str | None
    ) -> MarcFieldUpdate | None:
        if not vendor == "BT SERIES" or not call_no:
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
        return MarcFieldUpdate(
            delete=True, tag="091", ind1=" ", ind2=" ", subfields=new_subfields
        )

    @staticmethod
    def update_order_fields(
        record: bibs.DomainBib, mapping: dict[str, Any]
    ) -> list[MarcFieldUpdate]:
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
                    MarcFieldUpdate(tag=tag, ind1=" ", ind2=" ", subfields=subfields)
                )
        return fields
