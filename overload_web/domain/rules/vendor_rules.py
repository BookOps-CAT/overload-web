"""Record updaters for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class VendorRules:
    def __init__(
        self,
        library: str,
        record_type: str,
        order_mapping: dict[str, Any],
        bib_id_tag: str,
        default_loc: str,
    ) -> None:
        self.record_type = record_type
        self.library = library
        self.order_mapping = order_mapping
        self.default_loc = default_loc
        self.bib_id_tag = bib_id_tag

    def fields_to_update(
        self,
        record: bibs.DomainBib,
        format: str | None,
        call_no: str | None,
        field: Any | None,
    ) -> list[Any]:
        """
        Update a bibliographic record.

        Args:
            record:
                A parsed bibliographic record
            template_data:
                A dictionary containing template data to be used in updating records.
                This kwarg is only used for order-level records.

        Returns:
            An updated records as a `DomainBib` object
        """
        updates: list[Any] = []

        if self.record_type == "cat":
            updates.extend(
                FieldRules.add_vendor_fields(
                    bib_fields=getattr(record.vendor_info, "bib_fields", []),
                )
            )
        elif self.record_type == "sel":
            updates.extend(
                FieldRules.update_order_fields(
                    orders=record.orders, mapping=self.order_mapping
                )
            )
            updates.append(
                FieldRules.add_command_tag_and_default_loc(
                    field=field, format=format, default_loc=self.default_loc
                )
            )
        else:
            updates.extend(
                FieldRules.update_order_fields(
                    orders=record.orders, mapping=self.order_mapping
                )
            )
        updates.append(FieldRules.add_bib_id(bib_id=record.bib_id, tag=self.bib_id_tag))
        if self.library == "nypl":
            updates.append(FieldRules.update_910_field(collection=record.collection))
            if record.collection == "BL" and self.record_type == "cat":
                updates.append(
                    FieldRules.update_bt_series_call_no(
                        call_no=call_no, vendor=record.vendor
                    )
                )
        return updates


@dataclass
class MarcFieldObj:
    delete: bool
    tag: str
    ind1: str
    ind2: str
    subfields: list[dict[str, str]]


class FieldRules:
    @staticmethod
    def add_bib_id(bib_id: str | None, tag: str) -> MarcFieldObj | None:
        if bib_id:
            return MarcFieldObj(
                delete=True,
                tag=tag,
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": bib_id}],
            )
        return None

    @staticmethod
    def add_command_tag_and_default_loc(
        format: str | None, default_loc: str | None, field: Any | None
    ) -> MarcFieldObj | None:
        if not format and not default_loc:
            return None
        if not field:
            if format:
                command_tag = f"*b2={format};"
                if default_loc:
                    command_tag = f"*b2={format};bn={default_loc};"
                else:
                    command_tag = f"*b2={format};"
                return MarcFieldObj(
                    delete=False,
                    tag="949",
                    ind1=" ",
                    ind2=" ",
                    subfields=[{"code": "a", "value": command_tag}],
                )
            return MarcFieldObj(
                delete=False,
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
            field["a"] = f"{command_tag}bn={default_loc};"
        else:
            field["a"] = f"{command_tag};bn={default_loc};"
        return None

    @staticmethod
    def add_vendor_fields(bib_fields: list[dict[str, Any]]) -> list[MarcFieldObj]:
        field_objs = []
        for field_data in bib_fields:
            field_objs.append(
                MarcFieldObj(
                    delete=False,
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
    def update_910_field(collection: str) -> MarcFieldObj:
        return MarcFieldObj(
            delete=True,
            tag="910",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": collection}],
        )

    @staticmethod
    def update_bt_series_call_no(
        vendor: str | None, call_no: str | None
    ) -> MarcFieldObj | None:
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
        return MarcFieldObj(
            delete=True, tag="091", ind1=" ", ind2=" ", subfields=new_subfields
        )

    @staticmethod
    def update_order_fields(
        orders: list[bibs.Order], mapping: dict[str, Any]
    ) -> list[MarcFieldObj]:
        fields = []
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
                fields.append(
                    MarcFieldObj(
                        delete=False, tag=tag, ind1=" ", ind2=" ", subfields=subfields
                    )
                )
        return fields
