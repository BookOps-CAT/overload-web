"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)


class MarcContext:
    def __init__(self, record: bibs.DomainBib) -> None:
        self.bib_rec: Bib = Bib(record.binary_data, library=str(record.library))  # type: ignore
        self.record = record


class OrderMarcContext(MarcContext):
    def __init__(
        self,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
        rules: dict[str, Any],
    ) -> None:
        super().__init__(record)
        self.template_data = template_data
        self.rules = rules


@dataclass
class LibraryContext:
    bib_rec: Bib
    bib_id: str | None
    vendor: str | None


class OrderUpdateStep(Protocol):
    def apply(self, ctx: OrderMarcContext) -> None: ...


class LibraryUpdateStep(Protocol):
    def apply(self, ctx: LibraryContext) -> None: ...


class FullRecordUpdateStep(Protocol):
    def apply(self, ctx: MarcContext) -> None: ...


class ApplyOrderTemplate:
    def apply(self, ctx: OrderMarcContext) -> None:
        ctx.record.apply_order_template(ctx.template_data)


class MapOrdersToMarc:
    def apply(self, ctx: OrderMarcContext) -> None:
        rules = ctx.rules["updater_rules"]
        for order in ctx.record.orders:
            order_data = order.map_to_marc(rules=rules)
            for tag, subfield_values in order_data.items():
                subfields = []
                for k, v in subfield_values.items():
                    if v is None:
                        continue
                    if isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                ctx.bib_rec.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )


class AddCommandTag:
    def apply(self, ctx: OrderMarcContext) -> None:
        if "format" in ctx.template_data:
            command_tag = False
            for field in ctx.bib_rec.get_fields("949"):
                if field.indicators == Indicators(" ", " ") and field.get(
                    "a", ""
                ).startswith("*"):
                    command_tag = True
            if not command_tag:
                command_field = Field(
                    tag="949",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value=f"*b2={ctx.template_data['format']};")
                    ],
                )
                ctx.bib_rec.add_ordered_field(command_field)


class SetDefaultLocation:
    def apply(self, ctx: OrderMarcContext) -> None:
        default_loc = ctx.rules["default_locations"][ctx.bib_rec.library].get(
            ctx.bib_rec.collection
        )
        if not default_loc:
            return None
        for field in ctx.bib_rec.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                command = field["a"].strip()
                if "bn=" in command:
                    ctx.bib_rec.add_ordered_field(field)
                    return None
                else:
                    if command[-1] == ";":
                        new_command = f"{field['a']}bn={default_loc};"
                    else:
                        new_command = f"{field['a']};bn={default_loc};"

                    field["a"] = new_command
                    ctx.bib_rec.add_ordered_field(field)
                    return None
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*bn={default_loc};")],
        )
        ctx.bib_rec.add_ordered_field(field)


class Remove910Field:
    def apply(self, ctx: LibraryContext):
        ctx.bib_rec.remove_fields("910")


class AddBibId:
    def __init__(self, tag: str):
        self.tag = tag

    def apply(self, ctx: LibraryContext):
        if ctx.bib_id:
            ctx.bib_rec.remove_fields(self.tag)
            ctx.bib_rec.add_ordered_field(
                Field(
                    tag=self.tag,
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=ctx.bib_id)],
                )
            )


class UpdateLeader:
    def apply(self, ctx: LibraryContext):
        ctx.bib_rec.leader = ctx.bib_rec.leader[:9] + "a" + ctx.bib_rec.leader[10:]


class UpdateBtSeriesCallNo:
    def apply(self, ctx: LibraryContext):
        if not (
            ctx.bib_rec.collection == "BL"
            and ctx.vendor == "BT SERIES"
            and "091" in ctx.bib_rec
        ):
            return None
        new_callno_subfields = []
        pos = 0
        callno = ctx.bib_rec.get_fields("091")[0].value()

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
                "Constructed call number does not match original."
                f"New={callno}, Original={field.value()}"
            )
        ctx.bib_rec.remove_fields(field.tag)
        ctx.bib_rec.add_ordered_field(field)


class AddVendorFields:
    def apply(self, ctx: MarcContext) -> None:
        bib_fields = getattr(ctx.record.vendor_info, "bib_fields", [])
        for field_data in bib_fields:
            ctx.bib_rec.add_ordered_field(
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


class BookopsMarcUpdateHandler:
    def __init__(self) -> None:
        self.full_record_pipelines = {"cat": [AddVendorFields()]}
        self.order_pipelines = {
            "acq": [ApplyOrderTemplate(), MapOrdersToMarc()],
            "sel": [
                ApplyOrderTemplate(),
                MapOrdersToMarc(),
                AddCommandTag(),
                SetDefaultLocation(),
            ],
        }
        self.library_pipelines = {
            "nypl": [
                Remove910Field(),
                AddBibId(tag="945"),
                UpdateBtSeriesCallNo(),
                UpdateLeader(),
            ],
            "bpl": [AddBibId(tag="907"), UpdateLeader()],
        }

    def create_order_marc_ctx(
        self,
        record: bibs.DomainBib,
        rules: dict[str, Any],
        template_data: dict[str, Any],
    ) -> OrderMarcContext:
        return OrderMarcContext(record=record, template_data=template_data, rules=rules)

    def create_library_ctx(
        self, bib_id: str | None, bib_rec: Bib, vendor: str | None
    ) -> LibraryContext:
        return LibraryContext(bib_rec=bib_rec, bib_id=bib_id, vendor=vendor)

    def create_full_marc_ctx(self, record: bibs.DomainBib) -> MarcContext:
        return MarcContext(record=record)
