"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BookopsMarcUpdater:
    """Update MARC records based on attributes of domain objects."""

    def __init__(self, record_type: str, rules: dict[str, Any]) -> None:
        """
        Initialize a `BookopsMarcUpdater` using a specific set of marc mapping rules.

        This class is a concrete implementation of the `MarcUpdater` protocol.

        Args:
            record_type:
                the workflow to use to update the records (ie. 'acq', 'cat' or 'sel')
            rules:
                A dictionary containing set of rules to use when mapping `Order`
                objects to MARC records. These rules map attributes of an `Order` to
                MARC fields and subfields.
        """
        self.record_type = record_type
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

    def set_nypl_default_location(self, collection: str, bib: Bib) -> Field | None:
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

    def check_command_tag(self, bib_rec: Bib) -> bool:
        for field in bib_rec.get_fields("949"):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return True
        return False

    def db_template_to_949(self, mat_format: str) -> Field:
        field = Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*b2={mat_format};")],
        )
        return field

    def update_bib(self, bib_rec: Bib, bib_id: str | None) -> Bib:
        if bib_id:
            bib_id_field = self._create_bib_id_field(bib_id, library=bib_rec.library)
            bib_rec.remove_fields(bib_id_field.tag)
            bib_rec.add_ordered_field(bib_id_field)
        bib_rec.leader = bib_rec.leader[:9] + "a" + bib_rec.leader[10:]
        return bib_rec

    def update_nypl_record_data(self, bib_rec: Bib, vendor: str | None) -> Bib:
        fields = []
        field_910 = self._create_910_field(bib_rec.collection)
        bib_rec.remove_fields("910")
        fields.append(field_910)
        if "001" in bib_rec:
            control_no_field = Field(tag="001", data=str(bib_rec["001"]).lstrip("ocmn"))
            bib_rec.remove_fields(control_no_field.tag)
            bib_rec.add_ordered_field(control_no_field)
        if bib_rec.collection == "BL" and vendor == "BT SERIES" and "091" in bib_rec:
            new_call_no = self.update_bt_series_call_no(bib_rec)
            bib_rec.remove_fields(new_call_no.tag)
            fields.append(new_call_no)
        for field in fields:
            if field:
                bib_rec.add_ordered_field(field)
        return bib_rec

    def add_vendor_bib_fields(
        self, bib_rec: Bib, bib_fields: list[dict[str, Any]]
    ) -> Bib:
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

    def update_order(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> Bib:
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        record.apply_order_template(template_data=template_data)
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

    def output_record(sewlf, bib_rec: Bib, record: bibs.DomainBib) -> bibs.DomainBib:
        record.binary_data = bib_rec.as_marc()
        return record

    def update_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> Bib:
        bib_rec = self.update_order(record=record, template_data=template_data)
        bib_rec = self.update_bib(bib_rec=bib_rec, bib_id=record.bib_id)
        return bib_rec

    def update_bpl_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = self.update_acquisitions_record(
            record=record, template_data=template_data
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_nypl_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = self.update_acquisitions_record(
            record=record, template_data=template_data
        )
        bib_rec = self.update_nypl_record_data(
            bib_rec=bib_rec, vendor=template_data.get("vendor")
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_cataloging_record(self, record: bibs.DomainBib) -> Bib:
        bib_fields = getattr(record.vendor_info, "bib_fields", [])
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        bib_rec = self.add_vendor_bib_fields(bib_rec=bib_rec, bib_fields=bib_fields)
        bib_rec = self.update_bib(bib_rec=bib_rec, bib_id=record.bib_id)
        return bib_rec

    def update_bpl_cataloging_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        bib_rec = self.update_cataloging_record(record=record)
        record.binary_data = bib_rec.as_marc()
        return record

    def update_nypl_cataloging_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        bib_rec = self.update_cataloging_record(record=record)
        bib_rec = self.update_nypl_record_data(bib_rec=bib_rec, vendor=record.vendor)
        record.binary_data = bib_rec.as_marc()
        return record

    def update_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> Bib:
        bib_rec = self.update_order(record=record, template_data=template_data)
        if "format" in template_data and not self.check_command_tag(bib_rec=bib_rec):
            bib_rec.add_ordered_field(self.db_template_to_949(template_data["format"]))
        bib_rec = self.update_bib(bib_rec=bib_rec, bib_id=record.bib_id)
        return bib_rec

    def update_nypl_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = self.update_selection_record(
            record=record, template_data=template_data
        )
        bib_rec = self.update_nypl_record_data(bib_rec=bib_rec, vendor=record.vendor)
        bib_rec.add_ordered_field(
            self.set_nypl_default_location(
                bib=bib_rec, collection=str(record.collection)
            )
        )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_bpl_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        bib_rec = self.update_selection_record(
            record=record, template_data=template_data
        )
        record.binary_data = bib_rec.as_marc()
        return record
