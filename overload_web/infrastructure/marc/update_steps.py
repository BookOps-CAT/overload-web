from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class MarcFields:
    @staticmethod
    def add_field(
        bib: Bib, tag: str, ind1: str, ind2: str, subfields: list[dict[str, str]]
    ) -> None:
        bib.add_ordered_field(
            Field(
                tag=tag,
                indicators=Indicators(ind1, ind2),
                subfields=[
                    Subfield(code=i["code"], value=i["value"]) for i in subfields
                ],
            )
        )

    @staticmethod
    def delete_field(bib: Bib, tag: str) -> None:
        bib.remove_fields(tag)

    @staticmethod
    def _add_bib_id(bib: Bib, bib_id: str | None, tag: str):
        if bib_id:
            MarcFields.delete_field(bib=bib, tag=tag)
            MarcFields.add_field(
                bib=bib,
                tag=tag,
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": bib_id}],
            )

    @staticmethod
    def _add_command_tag(bib: Bib, format: str | None) -> None:
        if format:
            command_tag = False
            for field in bib.get_fields("949"):
                if field.indicators == Indicators(" ", " ") and field.get(
                    "a", ""
                ).startswith("*"):
                    command_tag = True
            if not command_tag:
                MarcFields.add_field(
                    bib=bib,
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": f"*b2={format};"}],
                )

    @staticmethod
    def _add_vendor_fields(bib: Bib, bib_fields: list[dict[str, Any]]) -> None:
        for field_data in bib_fields:
            MarcFields.add_field(
                bib=bib,
                tag=field_data["tag"],
                ind1=field_data["ind1"],
                ind2=field_data["ind2"],
                subfields=[{"code": field_data["code"], "value": field_data["value"]}],
            )

    @staticmethod
    def _set_default_location(bib: Bib, default_loc: str) -> None:
        if not default_loc:
            return None
        for field in bib.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                command = field["a"].strip()
                if "bn=" in command:
                    return None
                else:
                    if command[-1] == ";":
                        new_command = f"{field['a']}bn={default_loc};"
                    else:
                        new_command = f"{field['a']};bn={default_loc};"
                    field["a"] = new_command
                    return None
        MarcFields.add_field(
            bib=bib,
            tag="949",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": f"*bn={default_loc};"}],
        )

    @staticmethod
    def _update_leader(bib: Bib) -> None:
        bib.leader = bib.leader[:9] + "a" + bib.leader[10:]

    @staticmethod
    def _update_910_field(bib: Bib) -> None:
        MarcFields.delete_field(bib=bib, tag="910")
        MarcFields.add_field(
            bib=bib,
            tag="910",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": f"{bib.collection}"}],
        )

    @staticmethod
    def _update_bt_series_call_no(
        bib: Bib, collection: str, vendor: str | None, record_type: str
    ) -> None:
        if not (
            collection == "BL"
            and vendor == "BT SERIES"
            and "091" in bib
            and record_type == "cat"
        ):
            return None
        new_subfields = []
        pos = 0
        callno = bib.get_fields("091")[0].value()

        if callno[:6] == "J SPA ":
            new_subfields.append({"code": "p", "value": "J SPA"})
        elif callno[:2] == "J ":
            new_subfields.append({"code": "p", "value": "J"})

        if "GRAPHIC " in callno:
            new_subfields.append({"code": "f", "value": "GRAPHIC"})
        elif "HOLIDAY " in callno:
            new_subfields.append({"code": "f", "value": "HOLIDAY"})
        elif "YR " in callno:
            new_subfields.append({"code": "f", "value": "YR"})

        if "GN FIC " in callno:
            pos = callno.index("GN FIC ") + 7
            new_subfields.append({"code": "a", "value": "GN FIC"})
        elif "FIC " in callno:
            pos = callno.index("FIC ") + 4
            new_subfields.append({"code": "a", "value": "FIC"})
        elif "PIC " in callno:
            pos = callno.index("PIC ") + 4
            new_subfields.append({"code": "a", "value": "PIC"})
        elif callno[:4] == "J E ":
            pos = callno.index("J E ") + 4
            new_subfields.append({"code": "a", "value": "E"})
        elif callno[:8] == "J SPA E ":
            pos = callno.index("J SPA E ") + 8
            new_subfields.append({"code": "a", "value": "E"})

        new_subfields.append({"code": "c", "value": callno[pos:]})
        MarcFields.delete_field(bib=bib, tag="091")
        MarcFields.add_field(
            bib=bib, tag="091", ind1=" ", ind2=" ", subfields=new_subfields
        )

        new_call_no = bib.get_fields("091")[0].value()
        if callno != new_call_no:
            raise ValueError(
                "Constructed call number does not match original. "
                f"New={new_call_no}, Original={callno}"
            )

    @staticmethod
    def _update_order_fields(
        bib: Bib, orders: list[bibs.Order], mapping: dict[str, Any]
    ) -> None:
        for order in orders:
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
                MarcFields.add_field(
                    bib=bib, tag=tag, ind1=" ", ind2=" ", subfields=subfields
                )
