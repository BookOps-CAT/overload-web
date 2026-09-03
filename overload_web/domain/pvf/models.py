"""Classes that define domain entities."""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from overload_web.domain.shared import context, fields

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
        collection: context.Collection | str | None,
        library: context.LibrarySystem | str,
        parsed_fields: list[fields.ParsedField],
        record_type: context.RecordType | str,
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
            binary_data:
                The marc record as a byte literal or `bytes` object
            collection:
                The collection to whom the record belongs as an enum
                (`Collection`), str or None.
            library:
                The library to whom the record belongs as an enum
                (`LibrarySystem`), str, or None.
            record_type:
                The workflow two whom this record belongs as an enum
                (`RecordType`), str, or None.
            title:
                The title associated with the record as a string.
            barcodes:
                The list of barcodes associated with the bib record as strings.
            bib_id:
                The record's sierra bib ID as a string.
            branch_call_number:
                The branch call number for the record, if present.
            command_tag:
                The command tag from an incoming record if present.
            control_number:
                The record's control number as a string, if present.
            isbn:
                The ISBN for the title as a string, if present.
            oclc_number:
                OCLC number(s) identifying the record as a string or list of strings,
                if present.
            orders:
                The list of orders associated with the record as `Order` domain objects.
            research_call_number:
                The research call number for the record as a string or list of strings,
                if present.
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
        self.collection = context.Collection(str(collection).upper())
        self.command_tag = command_tag
        self.control_number = control_number
        self.isbn = isbn
        self.library = context.LibrarySystem(library)
        self.oclc_number = oclc_number
        self.orders = orders
        self.parsed_fields = parsed_fields
        self.research_call_number = research_call_number
        self.record_type = context.RecordType(record_type)
        self.title = title
        self.upc = upc
        self.update_date = update_date
        self.vendor_info = vendor_info
        self.vendor = vendor if not vendor_info else vendor_info.name
        self._action: CatalogAction | None = None

    @property
    def action(self) -> CatalogAction:
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

    def apply_match(self, action: CatalogAction, target_bib_id: str | None) -> None:
        """
        Update a `DomainBib` object's bib_id.

        Args:
            action: the action to take determined by match analysis
            target_bib_id: The new sierra bib ID if applicable as a string.

        Returns:
            None
        """
        if target_bib_id and self.bib_id is None:
            self.bib_id = target_bib_id
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


@dataclass
class VendorInfo:
    """A dataclass to define a vendor rules as an entity"""

    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str
    vendor_tags: list[dict[str, str]] | None = None
