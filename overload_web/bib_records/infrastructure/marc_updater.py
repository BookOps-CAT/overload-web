"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BookopsMarcFieldFactory:
    def check_command_tag(self, bib_rec: Bib) -> bool:
        for field in bib_rec.get_fields("949"):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return True
        return False

    def create_bib_id_field(self, bib_id: str, tag: str) -> Field:
        return Field(
            tag=tag,
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f".b{bib_id.strip('.b')}")],
        )

    def create_910_field(self, collection: str | None) -> Field | None:
        """Creates 910 for NYPL records with code for Research or Branches"""
        if collection:
            return Field(
                tag="910",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=collection)],
            )
        return None

    def update_leader(self, bib_rec: Bib) -> Bib:
        bib_rec.leader = bib_rec.leader[:9] + "a" + bib_rec.leader[10:]
        return bib_rec

    def update_bt_series_call_no(self, record: Bib) -> Field:
        new_callno_subfields = []
        pos = 0
        callno = record.get_fields("091")[0].value()

        # langugage and audience prefix
        if callno[:6] == "J SPA ":
            new_callno_subfields.append(Subfield(code="p", value="J SPA"))
        elif callno[:2] == "J ":
            new_callno_subfields.append(Subfield(code="p", value="J"))

        # format prefix
        if "GRAPHIC " in callno:
            new_callno_subfields.append(Subfield(code="f", value="GRAPHIC"))
        elif "HOLIDAY " in callno:
            new_callno_subfields.append(Subfield(code="f", value="HOLIDAY"))
        elif "YR " in callno:
            new_callno_subfields.append(Subfield(code="f", value="YR"))

        # main subfield
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

        # cutter subfield
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
        return field

    def set_nypl_default_location(self, bib_rec: Bib, default_loc: str) -> Field | None:
        for field in bib_rec.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                command = field["a"].strip()
                if "bn=" in command:
                    return field
                else:
                    if command[-1] == ";":
                        new_command = f"{field['a']}bn={default_loc};"
                    else:
                        new_command = f"{field['a']};bn={default_loc};"

                    field["a"] = new_command
                    return field
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*bn={default_loc};")],
        )
        return field

    def add_command_tag(self, mat_format: str) -> Field:
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*b2={mat_format};")],
        )
        return field


class NYPLStrategy:
    def __init__(self, field_factory: BookopsMarcFieldFactory):
        self.field_factory = field_factory

    def apply_library_updates(
        self, bib_rec: Bib, bib_id: str | None, vendor: str | None
    ) -> None:
        fields = []
        field_910 = self.field_factory.create_910_field(bib_rec.collection)
        bib_rec.remove_fields("910")
        fields.append(field_910)
        if bib_id:
            bib_id_field = self.field_factory.create_bib_id_field(bib_id, tag="945")
            bib_rec.remove_fields(bib_id_field.tag)
            fields.append(bib_id_field)
        if "001" in bib_rec:
            control_no_field = Field(tag="001", data=str(bib_rec["001"]).lstrip("ocmn"))
            bib_rec.remove_fields(control_no_field.tag)
            fields.append(control_no_field)
        if bib_rec.collection == "BL" and vendor == "BT SERIES" and "091" in bib_rec:
            new_call_no = self.field_factory.update_bt_series_call_no(bib_rec)
            bib_rec.remove_fields(new_call_no.tag)
            fields.append(new_call_no)
        for field in fields:
            if field:
                bib_rec.add_ordered_field(field)
        self.field_factory.update_leader(bib_rec=bib_rec)


class BPLStrategy:
    def __init__(self, field_factory: BookopsMarcFieldFactory):
        self.field_factory = field_factory

    def apply_library_updates(
        self, bib_rec: Bib, bib_id: str | None, vendor: str | None
    ) -> None:
        if bib_id:
            bib_id_field = self.field_factory.create_bib_id_field(bib_id, tag="907")
            bib_rec.remove_fields(bib_id_field.tag)
            bib_rec.add_ordered_field(bib_id_field)
        self.field_factory.update_leader(bib_rec=bib_rec)


class NYPLSelectionStrategy:
    def __init__(self, field_factory: BookopsMarcFieldFactory, rules: dict[str, Any]):
        self.field_factory = field_factory
        self.rules = rules

    def apply_updates(self, bib_rec: Bib) -> None:
        self.field_factory.set_nypl_default_location(
            default_loc=self.rules[str(bib_rec.collection)], bib_rec=bib_rec
        )


class OrderLevelStrategy:
    def __init__(self, field_factory: BookopsMarcFieldFactory, rules: dict[str, Any]):
        self.field_factory = field_factory
        self.rules = rules

    def apply_order_updates(
        self,
        bib_rec: Bib,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
    ) -> None:
        record.apply_order_template(template_data=template_data)
        for order in record.orders:
            order_data = order.map_to_marc(rules=self.rules)
            for tag in order_data.keys():
                subfields = []
                for k, v in order_data[tag].items():
                    if v is None:
                        continue
                    elif isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                bib_rec.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )

    def apply_acquisitions_updates(
        self,
        bib_rec: Bib,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
    ) -> None:
        self.apply_order_updates(
            bib_rec=bib_rec, record=record, template_data=template_data
        )

    def apply_selection_updates(
        self,
        bib_rec: Bib,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
    ) -> None:
        self.apply_order_updates(
            bib_rec=bib_rec, record=record, template_data=template_data
        )
        if "format" in template_data and not self.field_factory.check_command_tag(
            bib_rec=bib_rec
        ):
            bib_rec.add_ordered_field(
                self.field_factory.add_command_tag(template_data["format"])
            )


class FullLevelStrategy:
    def __init__(self, field_factory: BookopsMarcFieldFactory):
        self.field_factory = field_factory

    def apply_cataloging_updates(
        self, bib_rec: Bib, bib_fields: list[dict[str, Any]]
    ) -> None:
        for field in bib_fields:
            bib_rec.add_ordered_field(
                Field(
                    tag=field["tag"],
                    indicators=Indicators(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=field["subfield_code"], value=field["value"])
                    ],
                )
            )


class BookopsMarcUpdater:
    """Update MARC records based on attributes of domain objects."""

    def __init__(self, rules: dict[str, Any]) -> None:
        """
        Initialize a `BookopsMarcUpdater` using a specific set of marc mapping rules.

        This class is a concrete implementation of the `MarcUpdater` protocol.

        Args:
            rules:
                A dictionary containing set of rules to use when mapping `Order`
                objects to MARC records. These rules map attributes of an `Order` to
                MARC fields and subfields.
        """
        self.rules = rules
        self.field_factory = BookopsMarcFieldFactory()
        self.library_strategies: dict[str, NYPLStrategy | BPLStrategy] = {
            "nypl": NYPLStrategy(self.field_factory),
            "bpl": BPLStrategy(self.field_factory),
        }
        self.full_record_strategy = FullLevelStrategy(self.field_factory)
        self.order_record_strategy = OrderLevelStrategy(
            self.field_factory, rules=self.rules["updater_rules"]
        )
        self.nypl_sel_strategy = NYPLSelectionStrategy(
            field_factory=self.field_factory,
            rules=self.rules["default_locations"]["options"],
        )

    def update_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore

        self.order_record_strategy.apply_acquisitions_updates(
            bib_rec=bib_rec, record=record, template_data=template_data
        )
        library_strategy = self.library_strategies[str(record.library)]
        library_strategy.apply_library_updates(
            bib_rec, bib_id=record.bib_id, vendor=template_data.get("vendor")
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore

        self.order_record_strategy.apply_acquisitions_updates(
            bib_rec=bib_rec, record=record, template_data=template_data
        )
        library_strategy = self.library_strategies[str(record.library)]
        library_strategy.apply_library_updates(
            bib_rec, bib_id=record.bib_id, vendor=template_data.get("vendor")
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_cataloging_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        self.full_record_strategy.apply_cataloging_updates(
            bib_rec=bib_rec, bib_fields=getattr(record.vendor_info, "bib_fields", [])
        )
        library_strategy = self.library_strategies[str(record.library)]
        library_strategy.apply_library_updates(
            bib_rec, bib_id=record.bib_id, vendor=record.vendor
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        self.order_record_strategy.apply_selection_updates(
            bib_rec=bib_rec,
            record=record,
            template_data=template_data,
        )
        library_strategy = self.library_strategies[str(record.library)]
        library_strategy.apply_library_updates(
            bib_rec, bib_id=record.bib_id, vendor=template_data.get("vendor")
        )
        if str(record.library) == "nypl":
            self.nypl_sel_strategy.apply_updates(bib_rec=bib_rec)
        record.binary_data = bib_rec.as_marc()
        return record
