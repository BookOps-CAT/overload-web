"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict


class Collection(Enum):
    """Includes valid values for NYPL and BPL collection"""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"

    def __str__(self):
        return self.value


class DomainBib:
    """
    A domain model representing a bib record and its associated order data.

    Attributes:
        library: the library to whom the record belongs as an enum or str.
        binary_data: the marc record in binary (`bytes`)
        barcodes: list of barcodes associated with the record.
        bib_id: sierra bib ID.
        branch_call_number: branch call number for the record, if present.
        collection: the collection to whom the record belongs as an enum or str.
        control_number: the record's control number, if present.
        isbn: ISBN for the title, if present.
        oclc_number: OCLC number(s) identifying the record, if present.
        orders: list of orders associated with the record.
        research_call_number: research call number for the record, if present.
        title: the title associated with the record.
        upc: UPC number, if present.
        update_date: the date the record was last updated.
        vendor: the vendor to whom the record belongs, if applicable.
        vendor_info: info about the vendor as a `VendorInfo` object
    """

    def __init__(
        self,
        library: LibrarySystem | str,
        binary_data: bytes,
        barcodes: list[str] = [],
        bib_id: str | None = None,
        branch_call_number: str | list[str] | None = None,
        collection: Collection | str | None = None,
        control_number: str | None = None,
        isbn: str | None = None,
        oclc_number: str | list[str] | None = None,
        orders: list[Order] = [],
        research_call_number: str | list[str] | None = None,
        title: str | None = None,
        upc: str | None = None,
        update_date: datetime.datetime | str | None = None,
        vendor: str | None = None,
        vendor_info: VendorInfo | None = None,
    ) -> None:
        self.barcodes = barcodes
        self.bib_id = bib_id
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
        self.title = title
        self.upc = upc
        self.update_date = update_date
        self.vendor = vendor
        self.binary_data = binary_data
        self.vendor_info = vendor_info

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


class LibrarySystem(Enum):
    """Includes valid values for library system"""

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
        order_id: OrderId | str | None,
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
        self.order_id = OrderId(order_id) if isinstance(order_id, str) else order_id
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
        Apply template data to the order, updating any matching, non-empty fields.

        Args:
            template_data: Field-value pairs to apply.
        """
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)

    def map_to_marc(
        self, rules: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str | int | OrderId | list[str] | None]]:
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


@dataclass(frozen=True)
class OrderId:
    """A dataclass to define a OrderId as an entity"""

    value: str

    def __post_init__(self):
        """Validate that the order ID is a string"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("OrderId must be a non-empty string.")

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"OrderId(value={self.value!r})"


class RecordType(Enum):
    """Includes valid values for record type"""

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


class FetcherResponseDict(TypedDict):
    """Defines the dict returned by `BibFetcher.get_bibs_by_id` method"""

    barcodes: list[str]
    bib_id: str
    branch_call_number: list[str]
    cat_source: str
    collection: str | None
    control_number: str | None
    isbn: list[str]
    library: str
    oclc_number: list[str]
    research_call_number: list[str]
    title: str
    upc: list[str]
    update_date: str | None
    var_fields: list[dict[str, Any]]
