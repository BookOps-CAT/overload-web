from __future__ import annotations

from dataclasses import dataclass
import datetime
from typing import List, Optional, Union


class ModelBib:
    def __init__(
        self,
        bib_format: str,
        control_number: str,
        library: str,
        order_fixed_field: OrderFixedField,
        order_variable_field: OrderVariableField,
        bib_id: Optional[str] = None,
    ) -> None:
        self.bib_id = bib_id
        self.bib_format = bib_format
        self.control_number = control_number
        self.library = library
        self.order_fixed_field = order_fixed_field
        self.order_variable_field = order_variable_field

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelBib):
            return NotImplemented
        else:
            return (
                other.control_number == self.control_number
                and other.library == self.library
            )

    def merge_bib_id(self, other: ModelBib) -> None:
        if self == other and other.bib_id is not None:
            self.bib_id = other.bib_id


@dataclass
class OrderFixedField:
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
class OrderVariableField:
    internal_note: Optional[List[str]]
    isbn: Optional[List[str]]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]
    blanket_po: Optional[str]
