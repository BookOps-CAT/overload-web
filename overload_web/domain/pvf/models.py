"""Classes that define domain entities."""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Sequence

from overload_web.domain import shared

logger = logging.getLogger(__name__)


class CatalogAction(StrEnum):
    """Valid values for a cataloging action."""

    ATTACH = "attach"
    UPDATE = "update"
    INSERT = "insert"


class DomainBib:
    """A domain entity representing a bib record and its associated order data."""

    def __init__(
        self,
        binary_data: bytes,
        collection: shared.Collection | str | None,
        library: shared.LibrarySystem | str,
        parsed_fields: list[ParsedField] | list[dict[str, Any]],
        record_type: shared.RecordType | str,
        title: str,
        barcodes: list[str] = [],
        bib_id: str | None = None,
        branch_call_number: str | None = None,
        command_tag: str | None = None,
        control_number: str | None = None,
        isbn: str | None = None,
        oclc_number: str | list[str] | None = None,
        orders: list[Order] = [],
        research_call_number: str | list[str] | None = None,
        upc: str | None = None,
        update_date: str | None = None,
        vendor: str | None = None,
        vendor_info: VendorInfo | None = None,
    ) -> None:
        """
        Initialize a `DomainBib` object.

        Args:
            barcodes:
                The list of barcodes associated with the bib record as strings.
            bib_id:
                The record's sierra bib ID as a string.
            binary_data:
                The marc record as a byte literal or `bytes` object
            branch_call_number:
                The branch call number for the record, if present.
            collection:
                The collection to whom the record belongs as a
                `Collection` enum, str or None.
            command_tag:
                The command tag from an incoming record if present.
            control_number:
                The record's control number as a string, if present.
            isbn:
                The ISBN for the title as a string, if present.
            library:
                The library to whom the record belongs as a
                `LibrarySystem` enum, str, or None.
            oclc_number:
                OCLC number(s) identifying the record as a string or list of strings,
                if present.
            orders:
                The list of orders associated with the record as `Order` domain objects.
            record_type:
                The workflow two whom this record belongs as a
                `RecordType` enum, str, or None.
            research_call_number:
                The research call number for the record as a string or list of strings,
                if present.
            title:
                The title associated with the record as a string.
            upc:
                The UPC number associated with the record, if present.
            update_date:
                The date the record was last updated as a string following MARC 005
                formatting (ie. `YYYYMMDDHHMMSS.f`).
            vendor:
                The vendor to whom the record belongs as a string, if applicable.
            vendor_info:
                Info about the vendor as a `VendorInfo` object, if applicable.
        """

        self.barcodes = barcodes
        self.bib_id = bib_id
        self.binary_data = binary_data
        self.branch_call_number = branch_call_number
        self.collection = shared.Collection(collection).upper() if collection else None
        self.command_tag = command_tag
        self.control_number = control_number
        self.isbn = isbn
        self.library = shared.LibrarySystem(library)
        self.oclc_number = oclc_number
        self.orders = orders
        self.parsed_fields = [
            i if isinstance(i, ParsedField) else ParsedField(**i) for i in parsed_fields
        ]
        self.research_call_number = research_call_number
        self.record_type = shared.RecordType(record_type)
        self.title = title
        self.upc = upc
        self.update_date = update_date
        self.vendor_info = vendor_info
        self.vendor = vendor if not vendor_info else vendor_info.name
        self._action: str | None = None

    @property
    def action(self) -> str:
        """`CatalogAction` obj assigned bib after analysis. Only present after match."""
        if self._action is None:
            raise AttributeError("CatalogAction has not been assigned to the DomainBib")
        return self._action

    @action.setter
    def action(self, value) -> None:
        self._action = value

    @property
    def call_number(self) -> str | None:
        """Determine call number for bib record."""
        if self.library == "nypl" and self.collection == "RL":
            call_number = self.research_call_number
        else:
            call_number = self.branch_call_number
        if isinstance(call_number, list):
            call_number = call_number[0] if call_number else None
        return call_number

    @property
    def resource_id(self) -> str | None:
        """Determine resource ID for bib record."""
        if self.control_number:
            return self.control_number
        elif self.isbn:
            return self.isbn
        elif self.oclc_number and isinstance(self.oclc_number, str):
            return self.oclc_number
        elif self.oclc_number and isinstance(self.oclc_number, list):
            return self.oclc_number[0]
        elif self.upc:
            return self.upc
        return None

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Creates `datetime.datetime` object from `update_date` string."""
        if self.update_date:
            return datetime.datetime.strptime(self.update_date, "%Y%m%d%H%M%S.%f")
        return None

    def apply_match(self, action: str, bib_id: str | None) -> None:
        """
        Update a `DomainBib` object's bib_id.

        Args:
            action: the action to take determined by match analysis
            bib_id: The new sierra bib ID if applicable as a string.

        Returns:
            None
        """
        if bib_id and self.bib_id is None:
            self.bib_id = bib_id
        self._action = action

    def apply_order_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to all orders in this bib record.

        Args:
            template_data: dictionary of order fields and values to overwrite

        Returns:
            None
        """
        for order in self.orders:
            order.apply_template(template_data=template_data)

    def __repr__(self) -> str:
        return f"DomainBib(barcodes: {self.barcodes}, bib_id: {self.bib_id}, branch_call_number: {self.branch_call_number}, collection: {self.collection}, control_number: {self.control_number}, isbn: {self.isbn}, library: {self.library}, oclc_number: {self.oclc_number}, research_call_number: {self.research_call_number}, record_type: {self.record_type}, title: {self.title}, upc: {self.upc}, update_date: {self.update_date}, vendor: {self.vendor})"  # noqa: E501


class FieldUpdates:
    """Functions that create `MarcFieldUpdateValues` to be used to update MARC fields"""

    @staticmethod
    def add_bib_id(bib_id: str | None, tag: str) -> MarcFieldUpdateValues | None:
        """Creates a new bib ID field."""
        if bib_id:
            return MarcFieldUpdateValues(
                delete_fields_by_tag=True,
                tag=tag,
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": bib_id}],
            )
        return None

    @staticmethod
    def add_command_tag(
        format: str | None, default_loc: str | None, fields: list[ParsedField]
    ) -> MarcFieldUpdateValues | None:
        """Creates a new or updated command tag field."""
        if not format and not default_loc:
            return None
        command_tag: str | None = None
        for marc_field in fields:
            if marc_field.tag == "949" and marc_field.indicators == (" ", " "):
                for sf in marc_field.subfields:
                    if sf.code == "a" and sf.value[0] == "*" and command_tag is None:
                        command_tag = sf.value.strip()
                        if "bn=" in command_tag:
                            return None

        if not command_tag:
            if not format:
                command_tag = f"*bn={default_loc};"
            elif format and not default_loc:
                command_tag = f"*b2={format};"
            else:
                command_tag = f"*b2={format};bn={default_loc};"
            return MarcFieldUpdateValues(
                tag="949",
                ind1=" ",
                ind2=" ",
                subfields=[{"code": "a", "value": command_tag}],
            )
        if command_tag and not default_loc:
            return None
        return MarcFieldUpdateValues(
            tag="949",
            ind1=" ",
            ind2=" ",
            subfields=[
                {
                    "code": "a",
                    "value": f"{command_tag.removesuffix(';')};bn={default_loc};",
                }
            ],
            target_field_to_delete=TargetFieldCriteria(
                tag="949", indicators=(" ", " "), code="a", value=command_tag
            ),
        )

    @staticmethod
    def add_vendor_fields(fields: list[dict[str, Any]]) -> list[MarcFieldUpdateValues]:
        """Creates a list of fields for a full MARC record based on `VendorInfo`."""
        field_objs = []
        for field_data in fields:
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
    def get_item_field_criteria(
        fields: list[ParsedField], library: str
    ) -> tuple[str, str, str]:
        """Get appropriate item field tag and indicators."""
        if not library == "bpl":
            return ("949", " ", "1")
        fields_037 = [i for i in fields if i.tag == "037" and i.subfields]
        for marc_field in fields_037:
            subfield_a = []
            subfield_b: str | None = None
            for subfield in marc_field.subfields:
                if subfield.code == "a" and isinstance(subfield.value, str):
                    subfield_a.append(subfield.value)
                elif subfield.code == "b" and subfield.value == "OverDrive, Inc.":
                    subfield_b = subfield.value
            if subfield_b is not None and len(subfield_a) >= 1:
                return ("949", " ", "1")
        return ("960", " ", " ")

    @staticmethod
    def get_item_fields(
        fields: list[list[ParsedField]], criteria: tuple[str, str, str]
    ) -> list[MarcFieldUpdateValues]:
        """Creates list of item fields to add to combined duplicate records."""
        all_items = []
        for field_list in fields:
            for item in field_list:
                if item.tag == criteria[0] and item.indicators == (
                    criteria[1],
                    criteria[2],
                ):
                    all_items.append(
                        MarcFieldUpdateValues(
                            tag=item.tag,
                            ind1=item.indicators[0],
                            ind2=item.indicators[1],
                            subfields=[
                                {"code": i.code, "value": i.value}
                                for i in item.subfields
                            ],
                        )
                    )

        return all_items

    @staticmethod
    def update_910_field(collection: str) -> MarcFieldUpdateValues:
        """Adds 910 field for branches or research if applicable."""
        return MarcFieldUpdateValues(
            delete_fields_by_tag=True,
            tag="910",
            ind1=" ",
            ind2=" ",
            subfields=[{"code": "a", "value": collection}],
        )

    @staticmethod
    def update_bt_series_call_no(
        call_no: str | None, collection: str | None, vendor: str | None
    ) -> MarcFieldUpdateValues | None:
        """Updates call number for B&T Series materials."""
        if not vendor == "BT SERIES" or not call_no or not collection == "BL":
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
            delete_fields_by_tag=True,
            tag="091",
            ind1=" ",
            ind2=" ",
            subfields=new_subfields,
        )

    @staticmethod
    def update_order_fields(
        orders: Sequence[Order], mapping: dict[str, Any]
    ) -> list[MarcFieldUpdateValues]:
        """Updates order record fields based on template data applied to DomainBib"""
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
                    MarcFieldUpdateValues(
                        tag=tag, ind1=" ", ind2=" ", subfields=subfields
                    )
                )
        return fields


@dataclass
class MarcFieldUpdateValues:
    """Value object used to define updates to be made to a MARC field."""

    tag: str
    ind1: str
    ind2: str
    subfields: list[dict[str, str]]
    delete_fields_by_tag: bool = False
    target_field_to_delete: TargetFieldCriteria | None = None


@dataclass
class Order:
    """A domain model representing a Sierra order."""

    audience: list[str]
    blanket_po: str | None
    branches: list[str]
    copies: str | int | None
    country: str | None
    create_date: datetime.datetime | datetime.date | str | None
    format: str | None
    fund: str | None
    internal_note: str | None
    lang: str | None
    locations: list[str]
    order_code_1: str | None
    order_code_2: str | None
    order_code_3: str | None
    order_code_4: str | None
    order_id: str | None
    order_type: str | None
    price: str | int | None
    project_code: str | None
    selector_note: str | None
    shelves: list[str]
    status: str | None
    vendor_code: str | None
    vendor_notes: str | None
    vendor_title_no: str | None

    def apply_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to the order.

        Identifies fields based on the key of a key/value pair and overwrites
        it with the value from the key/value pair if the attribute is not empty.

        Args:
            template_data: Field-value pairs to apply.
        """
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)

    def map_to_marc(
        self, rules: dict[str, Any]
    ) -> dict[str, dict[str, str | int | list[str] | None]]:
        """
        Map order data to MARC using a set of mapping rules

        Args:
            rules: a dict defining the fields and subfields to map `Order` attributes to

        Returns:
            the attributes of the `Order` as a dict mapped to MARC fields and subfields
        """

        out = {}
        for key in rules.keys():
            tag_dict = {}
            for k, v in rules[key].items():
                tag_dict[k] = getattr(self, v)
            out[key] = tag_dict
        return out


class ParsedField:
    def __init__(
        self,
        tag: str,
        indicators: tuple[str, str] | None = None,
        subfields: list[ParsedSubfield] | list[dict[str, str]] = [],
        value: str | None = None,
    ):
        self.tag = tag
        self.indicators = indicators
        self.subfields = [
            i if isinstance(i, ParsedSubfield) else ParsedSubfield(**i)
            for i in subfields
        ]
        self.value = value


@dataclass(frozen=True)
class ParsedSubfield:
    """A pure Python representation of a MARC subfield."""

    code: str
    value: str


@dataclass
class TargetFieldCriteria:
    """Value object that defines data in a field to be deleted."""

    tag: str
    indicators: tuple[str, str]
    code: str
    value: str


@dataclass
class VendorInfo:
    """A dataclass to define a vendor rules as an entity"""

    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str
    vendor_tags: list[dict[str, str]] | None = None


class WorkflowStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    MATCHING = "MATCHING"
    UPDATING = "UPDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class WorkflowState:
    """Tracks the state of a long-running process."""

    id: str
    status: WorkflowStatus
    batch_id: str | None = None
    error_message: str | None = None
    record_type: str | None = None
    matchpoints: dict[str, str | None] = field(default_factory=dict)
    template_data: dict[str, Any] = field(default_factory=dict)
