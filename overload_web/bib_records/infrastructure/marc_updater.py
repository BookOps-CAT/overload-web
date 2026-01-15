"""Record updaters for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)


class MarcContext:
    def __init__(self, record: bibs.DomainBib, rules: dict[str, Any]) -> None:
        self.bib_rec: Bib = Bib(record.binary_data, library=record.library)  # type: ignore
        self.record = record
        self.order_mapping = rules["update_order_mapping"]
        self.default_loc = rules["default_locations"][self.bib_rec.library].get(
            self.bib_rec.collection
        )
        self.bib_id_tag = rules["bib_id_tag"][self.bib_rec.library]


class OrderMarcContext(MarcContext):
    def __init__(
        self,
        record: bibs.DomainBib,
        rules: dict[str, Any],
        template_data: dict[str, Any],
    ) -> None:
        super().__init__(record, rules)
        self.template_data = template_data


class UpdateStep(Protocol):
    def apply(self, ctx: Any) -> None: ...  # pragma: no branch


class MapOrderTemplateToMarc:
    def apply(self, ctx: OrderMarcContext) -> None:
        ctx.record.apply_order_template(ctx.template_data)
        for order in ctx.record.orders:
            order_data = order.map_to_marc(rules=ctx.order_mapping)
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
        if not ctx.default_loc:
            return None
        for field in ctx.bib_rec.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                command = field["a"].strip()
                if "bn=" in command:
                    return None
                else:
                    if command[-1] == ";":
                        new_command = f"{field['a']}bn={ctx.default_loc};"
                    else:
                        new_command = f"{field['a']};bn={ctx.default_loc};"
                    ctx.bib_rec.remove_field(field)
                    new_field = Field(
                        tag="949",
                        indicators=Indicators(" ", " "),
                        subfields=[Subfield(code="a", value=new_command)],
                    )
                    ctx.bib_rec.add_ordered_field(new_field)
                    return None
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*bn={ctx.default_loc};")],
        )
        ctx.bib_rec.add_ordered_field(field)


class Update910Field:
    def apply(self, ctx: MarcContext) -> None:
        ctx.bib_rec.remove_fields("910")
        field = Field(
            tag="910",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"{ctx.bib_rec.collection}")],
        )
        ctx.bib_rec.add_ordered_field(field)


class AddBibId:
    def apply(self, ctx: MarcContext) -> None:
        if ctx.record.bib_id:
            ctx.bib_rec.remove_fields(ctx.bib_id_tag)
            ctx.bib_rec.add_ordered_field(
                Field(
                    tag=ctx.bib_id_tag,
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=ctx.record.bib_id)],
                )
            )


class UpdateLeader:
    def apply(self, ctx: MarcContext) -> None:
        ctx.bib_rec.leader = ctx.bib_rec.leader[:9] + "a" + ctx.bib_rec.leader[10:]


class UpdateBtSeriesCallNo:
    def apply(self, ctx: MarcContext) -> None:
        if not (
            ctx.record.collection == "BL"
            and ctx.record.vendor == "BT SERIES"
            and "091" in ctx.bib_rec
            and ctx.record.record_type == "cat"
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
                "Constructed call number does not match original. "
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


StepFactory = Callable[[], UpdateStep]

WORKFLOW_PIPELINES: dict[str, list[StepFactory]] = {
    "acq": [MapOrderTemplateToMarc],
    "cat": [AddVendorFields],
    "sel": [MapOrderTemplateToMarc, AddCommandTag, SetDefaultLocation],
}
LIBRARY_PIPELINES: dict[str, list[StepFactory]] = {
    "nypl": [
        AddBibId,
        UpdateLeader,
        Update910Field,
        UpdateBtSeriesCallNo,
    ],
    "bpl": [AddBibId, UpdateLeader],
}


class BookopsMarcUpdateStrategy:
    def __init__(self, library: str, rules: dict[str, Any], record_type: str) -> None:
        self.rules = rules
        self.record_type = record_type
        self.library = library

    @property
    def pipeline(self) -> list[UpdateStep]:
        steps = WORKFLOW_PIPELINES[self.record_type] + LIBRARY_PIPELINES[self.library]
        return [step() for step in steps]

    def create_context(
        self,
        record: bibs.DomainBib,
        **kwargs: Any,
    ) -> MarcContext:
        if self.record_type in ["acq", "sel"]:
            return OrderMarcContext(
                record=record, rules=self.rules, template_data=kwargs["template_data"]
            )
        return MarcContext(record=record, rules=self.rules)
