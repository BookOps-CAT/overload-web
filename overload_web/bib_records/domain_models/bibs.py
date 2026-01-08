"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Collection(Enum):
    """Valid values for NYPL and BPL collections"""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"

    def __str__(self):
        return self.value


class DomainBib:
    """A domain model representing a bib record and its associated order data."""

    def __init__(
        self,
        binary_data: bytes,
        collection: Collection | str | None,
        library: LibrarySystem | str,
        title: str,
        record_type: RecordType | str,
        barcodes: list[str] = [],
        bib_id: str | None = None,
        branch_call_number: str | None = None,
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
            barcodes:
                The list of barcodes associated with the bib record as strings.
            bib_id:
                The record's sierra bib ID as a string.
            branch_call_number:
                The branch call number for the record, if present.
            collection:
                The collection to whom the record belongs as an enum (`Collection`)
                or str.
            control_number:
                The record's control number as a string, if present.
            isbn:
                The ISBN for the title as a string, if present.
            library:
                The library to whom the record belongs as an enum (`LibrarySystem`)
                or str.
            oclc_number:
                OCLC number(s) identifying the record as a string or list of strings,
                if present.
            orders:
                The list of orders associated with the record as `Order` domain objects.
            record_type:
                The workflow two whom this record belongs as an enum (`RecordType`)
                or str.
            research_call_number:
                The research call number for the record as a string or list of strings,
                if present.
            title:
                The title associated with the record.
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
        self.collection = (
            Collection(str(collection).upper())
            if not isinstance(collection, Collection)
            else collection
        )
        self.control_number = control_number
        self.isbn = isbn
        self.library = LibrarySystem(library) if isinstance(library, str) else library
        self.oclc_number = oclc_number
        self.orders = orders
        self.research_call_number = research_call_number
        self.record_type = (
            RecordType(record_type) if isinstance(record_type, str) else record_type
        )
        self.title = title
        self.upc = upc
        self.update_date = update_date
        self.vendor_info = vendor_info
        self.vendor = vendor if not vendor_info else vendor_info.name

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Creates `datetime.datetime` object from `update_date` string."""
        if self.update_date:
            return datetime.datetime.strptime(self.update_date, "%Y%m%d%H%M%S.%f")
        return None

    @update_datetime.setter
    def update_datetime(self, value: datetime.datetime | None) -> None:
        """
        Changes `update_date` if `update_datetime` is assigned a new value.
        The new `update_date` value will be formatted like a MARC 005 field
        (ie. `YYYYMMDDHHMMSS.f`).
        """
        if isinstance(value, datetime.datetime):
            self.update_date = datetime.datetime.strftime(value, "%Y%m%d%H%M%S.%f")
        else:
            self.update_date = value

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

    def update_bib_id(self, bib_id: str) -> None:
        """
        Update a `DomainBib` object's bib_id.

        Args:
            bib_id: The new sierra bib ID as a string.

        Returns:
            None
        """
        self.bib_id = bib_id


class LibrarySystem(Enum):
    """Valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"

    def __str__(self):
        return self.value


class Order:
    """A domain model representing a Sierra order."""

    def __init__(
        self,
        audience: list[str],
        blanket_po: str | None,
        branches: list[str],
        copies: str | int | None,
        country: str | None,
        create_date: datetime.datetime | datetime.date | str | None,
        format: str | None,
        fund: str | None,
        internal_note: str | None,
        lang: str | None,
        locations: list[str],
        order_code_1: str | None,
        order_code_2: str | None,
        order_code_3: str | None,
        order_code_4: str | None,
        order_id: str | None,
        order_type: str | None,
        price: str | int | None,
        selector_note: str | None,
        shelves: list[str],
        status: str | None,
        vendor_code: str | None,
        vendor_notes: str | None,
        vendor_title_no: str | None,
    ) -> None:
        self.audience = audience
        self.blanket_po = blanket_po
        self.branches = branches
        self.copies = copies
        self.country = country
        self.create_date = create_date
        self.format = format
        self.fund = fund
        self.internal_note = internal_note
        self.lang = lang
        self.locations = locations
        self.order_code_1 = order_code_1
        self.order_code_2 = order_code_2
        self.order_code_3 = order_code_3
        self.order_code_4 = order_code_4
        self.order_id = order_id
        self.order_type = order_type
        self.price = price
        self.selector_note = selector_note
        self.shelves = shelves
        self.status = status
        self.vendor_code = vendor_code
        self.vendor_notes = vendor_notes
        self.vendor_title_no = vendor_title_no

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


class RecordType(Enum):
    """Valid values for record type/processing workflow."""

    ACQUISITIONS = "acq"
    CATALOGING = "cat"
    SELECTION = "sel"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class VendorInfo:
    """A dataclass to define a vendor rules as an entity"""

    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str
