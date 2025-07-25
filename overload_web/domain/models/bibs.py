"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class BibId:
    """A dataclass to define a BibId as an entity"""

    value: str

    def __post_init__(self):
        """Validate that the Bib ID is a string"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("BibId must be a non-empty string.")

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"BibId(value={self.value!r})"


class Collection(Enum):
    """Includes valid values for NYPL and BPL collection"""

    BRANCH = "BL"
    RESEARCH = "RL"
    NONE = "NONE"

    def __str__(self):
        return self.value


@dataclass
class DomainBib:
    """
    A domain model representing a bib record and its associated order data.

    Attributes:
        library: the library to whom the record belongs as an enum.
        orders: list of orders associated with the record.
        bib_id: sierra bib ID.
        isbn: ISBN for the title, if present.
        oclc_number: OCLC number(s) identifying the record, if present.
        upc: UPC number, if present.
        call_number: call number for the record, if present.
        barcodes: list of barcodes associated with the record.
    """

    library: LibrarySystem
    orders: list[Order]
    bib_id: BibId | None = None
    isbn: str | None = None
    oclc_number: str | list[str] | None = None
    upc: str | None = None
    call_number: str | list[str] | None = None
    barcodes: list[str] = field(default_factory=list)

    def apply_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to all orders in this bib record.

        Args:
            template_data: dictionary of order fields and values to overwrite
        """
        for order in self.orders:
            order.apply_template(template_data=template_data)


class LibrarySystem(Enum):
    """Includes valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"

    def __str__(self):
        return self.value


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
    order_id: OrderId | None
    order_type: str | None
    price: str | int | None
    selector_note: str | None
    shelves: list[str]
    status: str | None
    var_field_isbn: str | None
    vendor_code: str | None
    vendor_notes: str | None
    vendor_title_no: str | None

    def apply_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to the order, updating any matching non-empty fields.

        Args:
            template_data: Field-value pairs to apply.
        """
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)


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

    FULL = "full"
    ORDER_LEVEL = "order_level"

    def __str__(self):
        return self.value
