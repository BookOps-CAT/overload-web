"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


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

    def _create_bib_id_field(self, bib_id: str, library: str) -> Field:
        bib_id = f".b{bib_id.strip('.b')}"
        if library == "bpl":
            return Field(
                tag="907",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=bib_id)],
            )
        else:
            return Field(
                tag="945",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=bib_id)],
            )

    def _create_910_field(self, collection: str | None) -> Field | None:
        """Creates 910 for NYPL records with code for Research or Branches"""
        if collection:
            return Field(
                tag="910",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=collection)],
            )
        return None

    def bib_patches(self, record: Bib) -> Field:
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

        # verify nothing has been lost
        if callno != field.value():
            raise ValueError(
                "Constructed call # does not match original."
                f"New={callno}, Original={field.value()}"
            )
        return field

    def set_nypl_sierra_bib_default_location(
        self, collection: str, bib: Bib
    ) -> Field | None:
        """
        adds a 949 MARC tag command for setting bibliographic location
        args:
            bib: pymarc.record.Record
        returns:
            bib: pymarc.record.Record, with added command "bn=" to
                the "949  $a" field, the field is created if missing
        """
        if collection == "BL":
            default_loc = self.rules["default_locations"]["options"]["branches"]
        else:
            default_loc = self.rules["default_locations"]["options"]["research"]

        # determine if 949 already preset
        for field in bib.get_fields("949", []):
            if (
                field.indicator1 == " "
                and field.indicator2 == " "
                and "a" in field
                and field["a"][0] == "*"
            ):
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

    def check_command_tag(self, bib_rec: Bib) -> bool:
        for field in bib_rec.get_fields("949"):
            if field.indicators == [" ", " "] and "a" in field and field["a"][0] == "*":
                return True
        return False

    def db_template_to_949(self, mat_format: str) -> Field:
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*b2={mat_format};")],
        )
        return field

    def update_record_data(
        self, bib_rec: Bib, bib_id: str | None, vendor: str | None
    ) -> Bib:
        """Update the bib_id and add MARC fields to a `bibs.DomainBib` object."""
        fields: list[Field | None] = []
        if bib_id:
            bib_id_field = self._create_bib_id_field(bib_id, library=bib_rec.library)
            bib_rec.remove_fields(bib_id_field.tag)
            fields.append(bib_id_field)
        if bib_rec.library == "nypl":
            if "001" in bib_rec:
                bib_rec.remove_fields("001")
                control_no_field = Field(
                    tag="001", data=str(bib_rec["001"]).lstrip("ocmn")
                )
                bib_rec.add_ordered_field(control_no_field)
            bib_rec.remove_fields("910")
            field_910 = self._create_910_field(bib_rec.collection)
            fields.append(field_910)
        if (
            bib_rec.library == "nypl"
            and bib_rec.collection == "BL"
            and vendor == "BT SERIES"
            and "091" in bib_rec
        ):
            bib_rec.remove_fields("091")
            new_call_no = self.bib_patches(bib_rec)
            fields.append(new_call_no)
        for field in fields:
            if field:
                bib_rec.add_ordered_field(field)
        return bib_rec

    def update_bib_data(self, bib_rec: Bib, bib_fields: list) -> Bib:
        """Add MARC fields for a vendor record to a `bibs.DomainBib` object."""
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
        return bib_rec

    def update_order(self, record: bibs.DomainBib, bib_rec: Bib) -> Bib:
        """Update the MARC order fields within a `bibs.DomainBib` object."""
        for order in record.orders:
            order_data = order.map_to_marc(rules=self.rules["updater_rules"])
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
        return bib_rec

    def update_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        record.apply_order_template(template_data=template_data)
        bib_rec = self.update_order(record=record, bib_rec=bib_rec)
        bib_rec = self.update_record_data(
            bib_rec=bib_rec, bib_id=record.bib_id, vendor=template_data.get("vendor")
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_cataloging_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        bib_fields = getattr(record.vendor_info, "bib_fields", [])
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        bib_rec = self.update_bib_data(bib_rec=bib_rec, bib_fields=bib_fields)
        bib_rec = self.update_record_data(
            bib_rec=bib_rec, bib_id=record.bib_id, vendor=record.vendor
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        record.apply_order_template(template_data=template_data)
        bib_rec = self.update_order(record=record, bib_rec=bib_rec)
        bib_rec = self.update_record_data(
            bib_rec=bib_rec, bib_id=record.bib_id, vendor=template_data.get("vendor")
        )
        if "format" in template_data and not self.check_command_tag(bib_rec=bib_rec):
            bib_rec.add_ordered_field(self.db_template_to_949(template_data["format"]))
        if str(record.library) == "nypl":
            bib_rec.add_ordered_field(
                self.set_nypl_sierra_bib_default_location(
                    str(record.collection), bib_rec
                )
            )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_bib(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        match str(record.record_type):
            case "cat":
                return self.update_cataloging_record(record=record)
            case "acq":
                return self.update_acquisitions_record(
                    record=record, template_data=template_data
                )
            case "sel":
                return self.update_selection_record(
                    record=record, template_data=template_data
                )
            case _:
                raise OverloadError("invalid record type")
