"""Domain models that define bib records and order records"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

import bookops_marc
import bookops_marc.models


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
    """Includes valid values for NYPL collection"""

    BRANCH = "BL"
    RESEARCH = "RL"

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
    bib_id: Optional[BibId] = None
    isbn: Optional[str] = None
    oclc_number: Optional[Union[str, list[str]]] = None
    upc: Optional[str] = None
    call_number: Optional[Union[str, list[str]]] = None
    barcodes: list[str] = field(default_factory=list)

    def apply_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to all orders in this bib record.

        Args:
            template_data: dictionary of order fields and values to overwrite
        """
        for order in self.orders:
            order.apply_template(template_data=template_data)

    @classmethod
    def from_marc(cls, bib: bookops_marc.Bib) -> DomainBib:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object.

        Args:
            bib: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            DomainBib: domain object populated with structured order and identifier data.
        """
        return DomainBib(
            library=LibrarySystem(bib.library),
            orders=[Order.from_marc(order=i) for i in bib.orders],
            bib_id=(BibId(value=bib.sierra_bib_id) if bib.sierra_bib_id else None),
            upc=bib.upc_number,
            isbn=bib.isbn,
            oclc_number=list(bib.oclc_nos.values()),
            barcodes=bib.barcodes,
            call_number=(
                bib.research_call_no if bib.collection == "RL" else bib.branch_call_no
            ),
        )


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
    blanket_po: Optional[str]
    branches: list[str]
    copies: Optional[Union[str, int]]
    country: Optional[str]
    create_date: Optional[Union[datetime.datetime, datetime.date, str]]
    format: Optional[str]
    fund: Optional[str]
    internal_note: Optional[str]
    lang: Optional[str]
    locations: list[str]
    order_code_1: Optional[str]
    order_code_2: Optional[str]
    order_code_3: Optional[str]
    order_code_4: Optional[str]
    order_id: Optional[OrderId]
    order_type: Optional[str]
    price: Optional[Union[str, int]]
    selector_note: Optional[str]
    shelves: list[str]
    status: Optional[str]
    var_field_isbn: Optional[str]
    vendor_code: Optional[str]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]

    def _marc_mapping(self) -> dict[str, Any]:
        """
        Returns a mapping of MARC field codes to the corresponding attributes
        in the `Order` dataclass.
        """
        return {
            "960": {
                "c": self.order_code_1,
                "d": self.order_code_2,
                "e": self.order_code_3,
                "f": self.order_code_4,
                "g": self.format,
                "i": self.order_type,
                "m": self.status,
                "o": self.copies,
                "q": self.create_date,
                "s": self.price,
                "t": self.locations,
                "u": self.fund,
                "v": self.vendor_code,
                "w": self.lang,
                "x": self.country,
                "z": self.order_id,
            },
            "961": {
                "d": self.internal_note,
                "f": self.selector_note,
                "h": self.vendor_notes,
                "i": self.vendor_title_no,
                "l": self.var_field_isbn,
                "m": self.blanket_po,
            },
        }

    def apply_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to the order, updating any matching non-empty fields.

        Args:
            template_data: Field-value pairs to apply.
        """
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)

    @classmethod
    def from_marc(cls, order: bookops_marc.models.Order) -> Order:
        """
        Factory method used to construct an `Order` object from a `bookops_marc.Order`
        object.

        Args:
            order: an order from a `bookops_marc.Bib` or `bookops_marc.Order` object

        Returns:
            Order: an instance of the domain order populated from MARC data.
        """

        def from_following_field(code: str):
            if order._following_field:
                return order._following_field.get(code, None)
            return None

        return Order(
            audience=order.audn,
            blanket_po=from_following_field("m"),
            branches=order.branches,
            copies=order.copies,
            country=order._field.get("x", None),
            create_date=order.created,
            format=order.form,
            fund=order._field.get("u", None),
            internal_note=from_following_field("d"),
            lang=order.lang,
            locations=order.locs,
            order_code_1=order._field.get("c", None),
            order_code_2=order._field.get("d", None),
            order_code_3=order._field.get("e", None),
            order_code_4=order._field.get("f", None),
            order_type=order._field.get("i", None),
            order_id=(OrderId(value=str(order.order_id)) if order.order_id else None),
            price=order._field.get("s", None),
            selector_note=from_following_field("f"),
            shelves=order.shelves,
            status=order.status,
            var_field_isbn=from_following_field("l"),
            vendor_code=order._field.get("v", None),
            vendor_notes=order.venNotes,
            vendor_title_no=from_following_field("i"),
        )


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
