from __future__ import annotations

from dataclasses import asdict, dataclass
import datetime
from typing import List, Optional, Union


def apply_template(bib: OrderBib, template: OrderTemplate) -> OrderBib:
    template_dict = asdict(template)
    for k, v in template_dict.items():
        if v:
            setattr(bib, k, v)
    return bib


def attach(order: Order, bib_id: str) -> OrderBib:
    bib = OrderBib(order=order)
    bib.bib_id = bib_id
    return bib


class OrderBib:
    def __init__(self, order: Order) -> None:
        self.upc = order.upc
        self.isbn = order.isbn
        self.library = order.library
        self.oclc_number = order.oclc_number
        self.bib_id = order.bib_id
        self.create_date = order.fixed_field.create_date
        self.locations = order.fixed_field.locations
        self.shelves = order.fixed_field.shelves
        self.price = order.fixed_field.price
        self.fund = order.fixed_field.fund
        self.copies = order.fixed_field.copies
        self.lang = order.fixed_field.lang
        self.country = order.fixed_field.country
        self.vendor_code = order.fixed_field.vendor_code
        self.format = order.fixed_field.format
        self.selector = order.fixed_field.selector
        self.audience = order.fixed_field.audience
        self.source = order.fixed_field.source
        self.order_type = order.fixed_field.order_type
        self.status = order.fixed_field.status
        self.internal_note = order.variable_field.internal_note
        self.var_field_isbn = order.variable_field.isbn
        self.vendor_notes = order.variable_field.vendor_notes
        self.vendor_title_no = order.variable_field.vendor_title_no
        self.blanket_po = order.variable_field.blanket_po


@dataclass
class Order:
    fixed_field: FixedOrderData
    library: str
    variable_field: VariableOrderData
    bib_id: Optional[Union[str, int]] = None
    upc: Optional[Union[str, int]] = None
    isbn: Optional[Union[str, int]] = None
    oclc_number: Optional[Union[str, int]] = None


@dataclass
class OrderTemplate:
    create_date: Optional[Union[datetime.datetime, str]]
    locations: Optional[List[str]]
    shelves: Optional[List[str]]
    price: Optional[Union[str, int]]
    fund: Optional[List[str]]
    copies: Optional[Union[str, int]]
    lang: Optional[str]
    country: Optional[str]
    vendor_code: Optional[str]
    format: Optional[str]
    selector: Optional[str]
    audience: Optional[List[str]]
    source: Optional[str]
    order_type: Optional[str]
    status: Optional[str]
    internal_note: Optional[List[str]]
    isbn: Optional[List[str]]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]
    blanket_po: Optional[str]


@dataclass
class FixedOrderData:
    create_date: Union[datetime.datetime, str]
    locations: List[str]
    shelves: List[str]
    price: Union[str, int]
    fund: List[str]
    copies: Union[str, int]
    lang: str
    country: str
    vendor_code: str
    format: str
    selector: str
    audience: List[str]
    source: str
    order_type: str
    status: str


@dataclass
class VariableOrderData:
    internal_note: Optional[List[str]]
    isbn: Optional[List[str]]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]
    blanket_po: Optional[str]
