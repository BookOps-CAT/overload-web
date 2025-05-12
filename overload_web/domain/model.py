"""Domain models that define bib records, order records, and associated objects."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import bookops_marc
import bookops_marc.models


@dataclass
class DomainBib:
    """
    A domain model representing a bib record and its associated order data.

    Attributes:
        library: the library to whom the record belongs.
        orders: list of orders associated with the record.
        bib_id: sierra bib ID.
        isbn: ISBN for the title, if present.
        oclc_number: OCLC number(s) identifying the record, if present.
        upc: UPC number, if present.
    """

    library: str
    orders: List[Order]
    bib_id: Optional[str] = None
    isbn: Optional[str] = None
    oclc_number: Optional[Union[str, List[str]]] = None
    upc: Optional[str] = None

    def apply_template(self, template_data: Dict[str, Any]) -> None:
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
            bib: `Bib` record represented as a `bookops_marc.Bib` object.

        Returns:
            DomainBib: domain object populated with structured order and identifier data.
        """
        orders = []
        for order in bib.orders:
            orders.append(Order.from_marc(order=order))
        return DomainBib(
            library=bib.library,
            orders=orders,
            bib_id=bib.sierra_bib_id,
            upc=bib.upc_number,
            isbn=bib.isbn,
            oclc_number=list(bib.oclc_nos.values()),
        )


@dataclass
class Matchpoints:
    """
    Represents a set of matchpoint values used for identifying duplicate records
    in Sierra.

    Attributes:
        primary: primary field to match on.
        secondary: secondary field to match on.
        tertiary: tertiary field to match on.
    """

    primary: Optional[str] = None
    secondary: Optional[str] = None
    tertiary: Optional[str] = None

    def __init__(self, *args, **kwargs):
        """
        Initialize `Matchpoints` from positional or keyword arguments.

        Raises:
            ValueError: If tertiary matchpoint is provided without a secondary.
        """
        if "tertiary" in kwargs and "secondary" not in kwargs and len(args) < 2:
            raise ValueError("Cannot have tertiary matchpoint without secondary.")

        values = list(args)
        for key in ["primary", "secondary", "tertiary"]:
            if key in kwargs:
                if len(values) < ["primary", "secondary", "tertiary"].index(key) + 1:
                    values.append(kwargs[key])

        while len(values) < 3:
            values.append(None)

        self.primary, self.secondary, self.tertiary = values[:3]

    def as_list(self) -> List[str]:
        """Return the matchpoints as a list"""
        return [i for i in (self.primary, self.secondary, self.tertiary) if i]

    def __composite_values__(self):
        return self.primary, self.secondary, self.tertiary

    def __eq__(self, other) -> bool:
        if not isinstance(other, Matchpoints):
            return NotImplemented
        return self.__composite_values__() == other.__composite_values__()

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


@dataclass
class Order:
    """A domain model representing a Sierra order."""

    audience: List[str]
    blanket_po: Optional[str]
    branches: List[str]
    copies: Optional[Union[str, int]]
    country: Optional[str]
    create_date: Optional[Union[datetime.datetime, datetime.date, str]]
    format: Optional[str]
    fund: Optional[str]
    internal_note: Optional[str]
    lang: Optional[str]
    locations: List[str]
    order_code_1: Optional[str]
    order_code_2: Optional[str]
    order_code_3: Optional[str]
    order_code_4: Optional[str]
    order_id: Optional[int]
    order_type: Optional[str]
    price: Optional[Union[str, int]]
    selector_note: Optional[str]
    shelves: List[str]
    status: Optional[str]
    var_field_isbn: Optional[str]
    vendor_code: Optional[str]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]

    def apply_template(self, template_data: Dict[str, Any]) -> None:
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
            order_id=order.oid,
            price=order._field.get("s", None),
            selector_note=from_following_field("f"),
            shelves=order.shelves,
            status=order.status,
            var_field_isbn=from_following_field("l"),
            vendor_code=order._field.get("v", None),
            vendor_notes=order.venNotes,
            vendor_title_no=from_following_field("i"),
        )


@dataclass(kw_only=True)
class Template:
    """
    A reusable template for applying consistent values to orders.

    Attributes:
        matchpoints: a `Matchpoints` object used to identify matched bibs in Sierra.

        All other fields correspond to those available in the `Order` domain model.
    """

    matchpoints: Matchpoints = field(default_factory=Matchpoints)
    agent: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None

    blanket_po: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    country: Optional[str] = None
    create_date: Optional[Union[datetime.datetime, datetime.date, str]] = None
    format: Optional[str] = None
    fund: Optional[str] = None
    internal_note: Optional[str] = None
    lang: Optional[str] = None
    order_code_1: Optional[str] = None
    order_code_2: Optional[str] = None
    order_code_3: Optional[str] = None
    order_code_4: Optional[str] = None
    order_type: Optional[str] = None
    price: Optional[Union[str, int]] = None
    selector_note: Optional[str] = None
    status: Optional[str] = None
    var_field_isbn: Optional[str] = None
    vendor_code: Optional[str] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None
