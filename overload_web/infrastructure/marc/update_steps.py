"""Record updaters for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class MarcFields:
    @staticmethod
    def _add_bib_id(bib_rec: Bib, bib_id: str | None, tag: str):
        if bib_id:
            bib_rec.remove_fields(tag)
            bib_rec.add_ordered_field(
                Field(
                    tag=tag,
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=bib_id)],
                )
            )

    @staticmethod
    def _add_command_tag(bib_rec: Bib, template_data: dict[str, Any]) -> None:
        if "format" in template_data:
            command_tag = False
            for field in bib_rec.get_fields("949"):
                if field.indicators == Indicators(" ", " ") and field.get(
                    "a", ""
                ).startswith("*"):
                    command_tag = True
            if not command_tag:
                command_field = Field(
                    tag="949",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value=f"*b2={template_data['format']};")
                    ],
                )
                bib_rec.add_ordered_field(command_field)

    @staticmethod
    def _add_vendor_fields(bib_rec: Bib, bib_fields: list[dict[str, Any]]) -> None:
        for field_data in bib_fields:
            bib_rec.add_ordered_field(
                Field(
                    tag=field_data["tag"],
                    indicators=Indicators(field_data["ind1"], field_data["ind2"]),
                    subfields=[
                        Subfield(
                            code=field_data["subfield_code"], value=field_data["value"]
                        )
                    ],
                )
            )

    @staticmethod
    def _apply_order_template(
        bib: bibs.DomainBib, template_data: dict[str, Any]
    ) -> None:
        bib.apply_order_template(template_data)

    @staticmethod
    def _set_default_location(bib_rec: Bib, default_loc: str) -> None:
        if not default_loc:
            return None
        for field in bib_rec.get_fields("949", []):
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
                    bib_rec.remove_field(field)
                    new_field = Field(
                        tag="949",
                        indicators=Indicators(" ", " "),
                        subfields=[Subfield(code="a", value=new_command)],
                    )
                    bib_rec.add_ordered_field(new_field)
                    return None
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*bn={default_loc};")],
        )
        bib_rec.add_ordered_field(field)

    @staticmethod
    def _update_leader(bib_rec: Bib) -> None:
        bib_rec.leader = bib_rec.leader[:9] + "a" + bib_rec.leader[10:]

    @staticmethod
    def _update_910_field(bib_rec: Bib) -> None:
        bib_rec.remove_fields("910")
        field = Field(
            tag="910",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"{bib_rec.collection}")],
        )
        bib_rec.add_ordered_field(field)

    @staticmethod
    def _update_bt_series_call_no(
        bib_rec: Bib, collection: str, vendor: str | None, record_type: str
    ) -> None:
        if not (
            collection == "BL"
            and vendor == "BT SERIES"
            and "091" in bib_rec
            and record_type == "cat"
        ):
            return None
        new_callno_subfields = []
        pos = 0
        callno = bib_rec.get_fields("091")[0].value()

        if callno[:6] == "J SPA ":
            new_callno_subfields.append(Subfield(code="p", value="J SPA"))
        elif callno[:2] == "J ":
            new_callno_subfields.append(Subfield(code="p", value="J"))

        if "GRAPHIC " in callno:
            new_callno_subfields.append(Subfield(code="f", value="GRAPHIC"))
        elif "HOLIDAY " in callno:
            new_callno_subfields.append(Subfield(code="f", value="HOLIDAY"))
        elif "YR " in callno:
            new_callno_subfields.append(Subfield(code="f", value="YR"))

        if "GN FIC " in callno:
            pos = callno.index("GN FIC ") + 7
            new_callno_subfields.append(Subfield(code="a", value="GN FIC"))
        elif "FIC " in callno:
            pos = callno.index("FIC ") + 4
            new_callno_subfields.append(Subfield(code="a", value="FIC"))
        elif "PIC " in callno:
            pos = callno.index("PIC ") + 4
            new_callno_subfields.append(Subfield(code="a", value="PIC"))
        elif callno[:4] == "J E ":
            pos = callno.index("J E ") + 4
            new_callno_subfields.append(Subfield(code="a", value="E"))
        elif callno[:8] == "J SPA E ":
            pos = callno.index("J SPA E ") + 8
            new_callno_subfields.append(Subfield(code="a", value="E"))

        new_callno_subfields.append(Subfield(code="c", value=callno[pos:]))
        field = Field(
            tag="091",
            indicators=Indicators(" ", " "),
            subfields=new_callno_subfields,
        )
        if callno != field.value():
            raise ValueError(
                "Constructed call number does not match original. "
                f"New={callno}, Original={field.value()}"
            )
        bib_rec.remove_fields(field.tag)
        bib_rec.add_ordered_field(field)

    @staticmethod
    def _update_order_fields(
        bib_rec: Bib, orders: list[bibs.Order], mapping: dict[str, Any]
    ) -> None:
        for order in orders:
            order_data = order.map_to_marc(rules=mapping)
            for tag, subfield_values in order_data.items():
                subfields = []
                for k, v in subfield_values.items():
                    if v is None:
                        continue
                    if isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                bib_rec.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )
