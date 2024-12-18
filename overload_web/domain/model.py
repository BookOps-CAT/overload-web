from __future__ import annotations

from dataclasses import dataclass
import datetime
from typing import List, Optional, Union


def attach(order_data: Order, matched_bib_id: str) -> OrderBib:
    order = OrderBib(order=order_data)
    order.bib_id = matched_bib_id
    return order


def match(
    order_data: Order, bib: OrderBib, matchpoints: List[str]
) -> Optional[Union[str, int]]:
    bib_id = None
    for match in matchpoints:
        if match == "bib_id" and order_data.bib_id == bib.bib_id:
            bib_id = bib.bib_id
        elif match == "oclc_number" and order_data.oclc_number == bib.oclc_number:
            bib_id = bib.bib_id
        elif match == "isbn" and order_data.isbn == bib.isbn:
            bib_id = bib.bib_id
        elif match == "upc" and order_data.upc == bib.upc:
            bib_id = bib.bib_id
        if bib_id:
            return bib_id
    return bib_id


class OrderBib:
    def __init__(self, order: Order, bib_id: Optional[Union[str, int]] = None) -> None:
        self.upc = order.upc
        self.isbn = order.isbn
        self.library = order.library
        self.oclc_number = order.oclc_number
        self.fixed_order_data = order.fixed_field
        self.variable_order_data = order.variable_field

        if not bib_id:
            self.bib_id = order.bib_id
        else:
            self.bib_id = bib_id

    def attach(self, bib_id: Union[str, int]) -> None:
        self.bib_id = bib_id


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
