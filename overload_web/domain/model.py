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
        self.audience = order.audience
        self.bib_id = order.bib_id
        self.blanket_po = order.blanket_po
        self.copies = order.copies
        self.country = order.country
        self.create_date = order.create_date
        self.format = order.format
        self.fund = order.fund
        self.internal_note = order.internal_note
        self.isbn = order.isbn
        self.lang = order.lang
        self.library = order.library
        self.locations = order.locations
        self.oclc_number = order.oclc_number
        self.order_type = order.order_type
        self.price = order.price
        self.selector = order.selector
        self.source = order.source
        self.status = order.status
        self.upc = order.upc
        self.var_field_isbn = order.isbn
        self.vendor_code = order.vendor_code
        self.vendor_notes = order.vendor_notes
        self.vendor_title_no = order.vendor_title_no

    def attach(self, bib_ids: List[str]) -> None:
        if bib_ids:
            self.bib_id = bib_ids[0]
            self.all_bib_ids = bib_ids
        else:
            self.all_bib_ids = []


@dataclass
class Order:
    audience: Optional[str]
    blanket_po: Optional[str]
    copies: Optional[Union[str, int]]
    country: Optional[str]
    create_date: Optional[datetime.date]
    format: Optional[str]
    fund: Optional[str]
    internal_note: Optional[str]
    lang: Optional[str]
    library: str
    locations: List[str]
    order_type: Optional[str]
    price: Optional[Union[str, int]]
    selector: Optional[str]
    source: Optional[str]
    status: Optional[str]
    var_field_isbn: Optional[str]
    vendor_code: Optional[str]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]

    bib_id: Optional[Union[str, int]] = None
    isbn: Optional[Union[str, int, List[str]]] = None
    oclc_number: Optional[Union[str, int, List[str]]] = None
    upc: Optional[Union[str, int, List[str]]] = None


@dataclass
class OrderTemplate:
    audience: Optional[str] = None
    blanket_po: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    country: Optional[str] = None
    create_date: Optional[Union[datetime.datetime, str]] = None
    format: Optional[str] = None
    fund: Optional[str] = None
    internal_note: Optional[str] = None
    lang: Optional[str] = None
    order_type: Optional[str] = None
    price: Optional[Union[str, int]] = None
    selector: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    var_field_isbn: Optional[str] = None
    vendor_code: Optional[str] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None

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
