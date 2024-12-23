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

    def attach(self, bib_ids: List[str]) -> None:
        if bib_ids:
            self.bib_id = bib_ids[0]
            self.all_bib_ids = bib_ids
        else:
            self.all_bib_ids = []


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
    create_date: Optional[Union[datetime.datetime, str]] = None
    locations: Optional[List[str]] = None
    shelves: Optional[List[str]] = None
    price: Optional[Union[str, int]] = None
    fund: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    lang: Optional[str] = None
    country: Optional[str] = None
    vendor_code: Optional[str] = None
    format: Optional[str] = None
    selector: Optional[str] = None
    audience: Optional[List[str]] = None
    source: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    internal_note: Optional[List[str]] = None
    isbn: Optional[List[str]] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None
    blanket_po: Optional[str] = None
    primary_matchpoint: Optional[str] = None
    secondary_matchpoint: Optional[str] = None
    tertiary_matchpoint: Optional[str] = None

    @property
    def matchpoints(self) -> List[str]:
        return [
            i
            for i in [
                self.primary_matchpoint,
                self.secondary_matchpoint,
                self.tertiary_matchpoint,
            ]
            if i
        ]


@dataclass
class FixedOrderData:
    create_date: Union[datetime.datetime, str]
    locations: List[str]
    shelves: List[str]
    price: Union[str, int]
    fund: str
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
